import json

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.crud.crud_alertgroup import alert_group
from app.crud.crud_alertgroup_schema import alert_group_schema
from app.crud.crud_entity import entity as entity_crud
from app.enums import TargetTypeEnum
from app.models.user import User
from app.models.alert import Alert, AlertData
from app.models.audit import Audit
from app.schemas.alert import AlertAdd, AlertCreate, AlertUpdate
from app.schemas.alertgroup import AlertGroupDetailedCreate
from app.schemas.flair import AlertFlairResult


class CRUDAlert(CRUDBase[Alert, AlertCreate, AlertUpdate]):
    def filter(self, query, filter_dict):
        query = self._promoted_to_or_from_filter(query, filter_dict, "to")

        return super().filter(query, filter_dict)

    def get_by_alert_group(
        self,
        db_session: Session,
        *,
        alert_group_id: int,
        skip: int = 0,
        limit: int = 100,
        audit_logger=None,
    ) -> list[Alert]:
        result = (
            db_session.query(self.model)
            .filter(Alert.alertgroup == alert_group_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        if audit_logger is not None:
            for item in result:
                audit_logger.log("read", item, log_thing=False)
        return result

    def create(self, db_session: Session, obj_in: AlertCreate, audit_logger=None):
        """
        Creates a single alert, possibly inside of a new alertgroup
        If you want to create an alert inside an existing alertgroup, you can
                probably use add_to_alert_group() instead.
        If you want to create multiple alerts inside a new alertgroup, use
                crud.alertgroup.create().
        """
        # Create an alertgroup for this alert if existing one not referenced
        if obj_in.alertgroup_id is None:
            new_alertgroup_subject = "<NO SUBJECT>"
            new_alertgroup_owner = obj_in.owner
            new_alertgroup_schema = alert_group.validate_alerts([obj_in])
            new_alertgroup = AlertGroupDetailedCreate(
                owner=new_alertgroup_owner,
                subject=new_alertgroup_subject,
                alert_schema=new_alertgroup_schema,
            )
            alertgroup = alert_group.create(
                db_session, obj_in=new_alertgroup, audit_logger=audit_logger
            )
            obj_in.alertgroup_id = alertgroup.id
        # Create the data cells
        schema_map = alert_group_schema.get_alertgroup_schema_map(
            db_session, obj_in.alertgroup_id
        )
        
        # Create the actual alert
        new_alert = Alert(
            owner=obj_in.owner,
            status=obj_in.status,
            tlp=obj_in.tlp,
            alertgroup_id=obj_in.alertgroup_id,
            parsed=obj_in.parsed,
        )
        if obj_in.data is not None:
            for data_value in obj_in.data:
                if data_value.name not in schema_map:
                    raise ValueError(
                        "Column %s not found in existing alert schema" % data_value.name
                    )
            data_cells = {
                d.name: AlertData(
                    schema_key_id=schema_map[d.name],
                    data_value=d.value,
                    data_value_flaired=d.value_flaired,
                )
                for d in obj_in.data
            }
            new_alert.data_cells.update(data_cells)

        db_session.add(new_alert)
        db_session.flush()
        db_session.refresh(new_alert)
        self.publish("create", new_alert)
        if audit_logger is not None:
            audit_logger.log("create", new_alert)
            audit_logger.log("update", new_alert,
                             thing_type=TargetTypeEnum.alertgroup,
                             thing_subtype=TargetTypeEnum.alert,
                             thing_pk=new_alert.alertgroup_id)
        return new_alert

    def update(self, db_session: Session, db_obj: Alert, obj_in: AlertUpdate, audit_logger=None):
        schema_map = alert_group_schema.get_alertgroup_schema_map(
            db_session, db_obj.alertgroup_id
        )
        # Update items in data/data_flaired
        if obj_in.data is not None:
            for key in obj_in.data:
                value = obj_in.data[key]
                if key in db_obj.data:
                    db_obj.data[key] = obj_in.data[key]
                else:
                    if key not in schema_map:
                        raise ValueError(
                            "Column '%s' not found in existing alert schema" % key
                        )
                    new_alertdata = AlertData(
                        schema_key_id=schema_map[key], data_value=value
                    )
                    db_obj.data_cells[key] = new_alertdata
        if obj_in.data_flaired is not None:
            for key in obj_in.data_flaired:
                value = obj_in.data_flaired[key]
                if key in db_obj.data:
                    db_obj.data_flaired[key] = obj_in.data_flaired[key]
                else:
                    if key not in schema_map:
                        raise ValueError(
                            "Column '%s' not found in existing alert schema" % key
                        )
                    new_alertdata = AlertData(
                        schema_key_id=schema_map[key], data_value_flaired=value
                    )
                    db_obj.data_cells[key] = new_alertdata
        # Audit log here so that we capture data/data_flaired
        if audit_logger is not None:
            audit_logger.log("update", obj_in.model_dump(exclude_unset=True),
                             thing_type=TargetTypeEnum.alert, thing_pk=db_obj.id)
            audit_logger.log("update",
                             obj_in.model_dump(exclude_unset=True).update({"id": db_obj.id}),
                             thing_type=TargetTypeEnum.alertgroup,
                             thing_subtype=TargetTypeEnum.alert,
                             thing_pk=db_obj.alertgroup_id)
        # Update all other fields as normal
        other_update_data = obj_in.model_dump(
            exclude={"data", "data_flaired"}, exclude_unset=True
        )
        # No audit log for super() because we already audit logged this
        return super().update(db_session, db_obj=db_obj, obj_in=other_update_data, audit_logger=None)

    def add_to_alert_group(
        self,
        db_session: Session,
        *,
        obj_in: AlertAdd,
        schema_map: dict | None = None,
        audit_logger=None
    ) -> Alert:
        # check if alertgroup exists before continuing
        _alertgroup = alert_group.get(db_session, obj_in.alertgroup_id)
        if not _alertgroup:
            raise ValueError("Alertgroup with %s no found" % obj_in.alertgroup_id)

        # Set owner to current user if owner not set
        if ("owner" not in obj_in.model_fields_set
                and audit_logger is not None):
            obj_in.owner = audit_logger.username

        # Create schema map from alertgroup if not given
        if schema_map is None:
            schema_map = alert_group_schema.get_alertgroup_schema_map(
                db_session, obj_in.alertgroup_id
            )
        # Compile data values
        alert_data = {}
        if obj_in.data is not None:
            for key in obj_in.data:
                if key not in schema_map:
                    raise ValueError("Column '%s' not found in existing alert schema" % key)
                alert_data[key] = AlertData(
                    schema_key_id=schema_map[key], data_value=obj_in.data[key]
                )
        if obj_in.data_flaired is not None:
            for key in obj_in.data_flaired:
                if key in alert_data:
                    alert_data[key].data_value_flaired = obj_in.data_flaired[key]
                elif key not in schema_map:
                    raise ValueError("Column '%s' not found in existing alert schema" % key)
                else:
                    alert_data[key] = AlertData(
                        schema_key_id=schema_map[key],
                        data_value_flaired=obj_in.data_flaired[key],
                    )
        # Create actual alert
        db_obj = Alert(
            owner=obj_in.owner,
            status=obj_in.status,
            tlp=obj_in.tlp,
            alertgroup_id=obj_in.alertgroup_id,
            parsed=obj_in.parsed,
        )
        db_obj.data_cells.update(alert_data)
        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)
        self.publish("create", db_obj)
        if audit_logger is not None:
            audit_logger.log("create", db_obj)
        return db_obj

    def undelete(
        self,
        db_session: Session,
        target_id: int | None = None,
        existing_data=None,
        keep_ids: bool = True,
        by_user: str | None = None,
        audit_logger=None,
    ):
        """
        Special undelete functionality for alerts, centered around undeleting
        AlertData objects
        """
        # Restore the alert as normal
        if existing_data is None:
            if target_id is None:
                raise ValueError("Must specify target id to restore")
            query = db_session.query(Audit).filter(
                (Audit.what == "delete")
                & (Audit.thing_type == TargetTypeEnum.alert.value)
                & (Audit.thing_id == target_id)
            )
            if by_user is not None:
                query = query.filter(Audit.username == by_user)
            audit = query.order_by(Audit.when_date.desc()).first()
            if not audit:
                raise ValueError("Target deleted alert not found")
            object_data = audit.audit_data
        else:
            object_data = existing_data
        restored_alert = super().undelete(
            db_session=db_session,
            existing_data=object_data,
            keep_ids=keep_ids,
            by_user=by_user,
            audit_logger=audit_logger,
        )
        # Restore all alertdata objects
        if "data_cells" in object_data:
            columns = inspect(AlertData).column_attrs
            for key, cell in object_data["data_cells"].items():
                restored_data = AlertData()
                for column in columns:
                    if column.key in cell and (keep_ids or "id" not in column.key):
                        setattr(restored_data, column.key, cell[column.key])
                if not keep_ids:
                    restored_data.alert_id = restored_alert.id
                    schema_map = alert_group_schema.get_alertgroup_schema_map(
                        db_session, restored_alert.alertgroup_id
                    )
                    restored_data.schema_key_id = schema_map.get(key)
                db_session.add(restored_data)
        db_session.flush()
        db_session.refresh(restored_alert)
        return restored_alert

    def flair_update(
        self,
        db_session: Session,
        alert_id: int,
        flair_result: AlertFlairResult,
        audit_logger=None,
    ):
        # We are serializing the json here now because of
        # issues getting serialized json back from the flair

        alert = self.get(db_session, alert_id)
        if alert is not None:
            if flair_result.flair_data is not None:
                for k, v in flair_result.flair_data.items():
                    flair_result.flair_data[k] = json.dumps(v)
                alert_update = AlertUpdate(data_flaired=flair_result.flair_data)
            else:
                alert_update = AlertUpdate()

            if flair_result.text_data is not None:
                for k, v in flair_result.text_data.items():
                    flair_result.text_data[k] = json.dumps(v)
                alert_update.data = flair_result.text_data
            self.update(db_session, alert, alert_update, audit_logger=audit_logger)
            if flair_result.entities is not None:
                for entity_type in flair_result.entities:
                    for entity in flair_result.entities[entity_type]:
                        entity_crud.link_entity_by_value(
                            db_session,
                            entity_value=entity,
                            target_type=TargetTypeEnum.alert,
                            target_id=alert_id,
                            entity_type=entity_type,
                            audit_logger=audit_logger,
                        )
        return alert


alert = CRUDAlert(Alert)
