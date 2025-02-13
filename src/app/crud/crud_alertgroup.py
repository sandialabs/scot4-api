import re

from collections import defaultdict
from datetime import datetime
from typing import Union, Dict
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import crud
from app.enums import PermissionEnum
from app.crud.base import CRUDBase
from app.crud.crud_permission import permission as crud_permission
from app.enums import TargetTypeEnum, TlpEnum, StatusEnum
from app.crud.crud_tag import tag
from app.crud.crud_source import source
from app.models import Signature, AlertGroup, AlertData, Audit, User, Permission, Alert
from app.schemas.alertgroup import (
    AlertGroupCreate,
    AlertGroupDetailedCreate,
    AlertGroupUpdate,
)
from app.schemas.alertgroupschema import AlertGroupSchemaColumnCreate
from app.schemas.flair import AlertFlairResult
from app.schemas.link import LinkCreate
from app.utils import escape_sql_like


class CRUDAlertGroup(CRUDBase[AlertGroup, AlertGroupDetailedCreate, AlertGroupUpdate]):
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "subject")

        status = filter_dict.pop("status", None)
        if status is not None:
            # don't need to do the () or [] filters, it should work either way
            if not isinstance(status, list) and not isinstance(status, tuple):
                status = [status]
            if StatusEnum.open in status:
                query = query.filter(AlertGroup.open_count > 0)
            if StatusEnum.closed in status:
                query = query.filter(AlertGroup.closed_count > 0)
            if StatusEnum.promoted in status:
                query = query.filter(AlertGroup.promoted_count > 0)

        not_status = filter_dict.get("not", {}).pop("status", None)
        if not_status is not None:
            # don't need to do the () or [] filters, it should work either way
            if not isinstance(not_status, list) and not isinstance(not_status, tuple):
                not_status = [not_status]
            if StatusEnum.open in not_status:
                query = query.filter(AlertGroup.open_count == 0)
            if StatusEnum.closed in not_status:
                query = query.filter(AlertGroup.closed_count == 0)
            if StatusEnum.promoted in not_status:
                query = query.filter(AlertGroup.promoted_count == 0)

        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)

    def create(
        self,
        db_session: Session,
        *,
        obj_in: Union[AlertGroupCreate, AlertGroupDetailedCreate],
        audit_logger=None,
    ) -> AlertGroup:
        """Create an alertgroup given an AlertGroupCreate Object
        First create the alertgroup. Get back the alertgroup ID.
        Next, create the alertgroup schema
        Next, create the alerts, with the given alertgroup ID.
        Fin

        """
        db_obj = AlertGroup(
            owner=obj_in.owner,
            tlp=obj_in.tlp,
            view_count=obj_in.view_count,
            first_view=obj_in.first_view,
            message_id=obj_in.message_id,
            subject=obj_in.subject,
            back_refs=obj_in.back_refs,
        )
        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)

        # Also create the schema and add alerts if detailed create
        if isinstance(obj_in, AlertGroupDetailedCreate):
            schema = None
            if obj_in.alert_schema:
                schema = obj_in.alert_schema
            # Create the schema if one wasn't given
            elif obj_in.alerts:
                schema = self.validate_alerts(obj_in.alerts)
            if schema is not None:
                # We have a valid schema, now let's add it
                for schema_column in schema:
                    schema_column.alertgroup_id = db_obj.id
                    crud.alert_group_schema.create(
                        db_session=db_session, obj_in=schema_column
                    )
                # We've now validated and added the schema, lets add the alerts now
                for alert in obj_in.alerts:
                    if alert.owner is None:
                        alert.owner = obj_in.owner
                    if alert.tlp == TlpEnum.unset:
                        alert.tlp = obj_in.tlp
                    alert.alertgroup_id = db_obj.id
                    crud.alert.create(db_session=db_session, obj_in=alert)
        self.publish("create", db_obj)
        # Check to see if the alert group subject is contained in
        # any existing signatures, if so, add links.
        if obj_in.subject is not None:
            looking_for = re.sub(r"\([^()]*\)", "", obj_in.subject)
            looking_for = re.sub("Splunk Alert:", "", looking_for)
            looking_for = escape_sql_like(looking_for.strip())
            if "*" in looking_for or "?" in looking_for:
                looking_for = (
                    looking_for.replace("*", "%").replace("?", "_")
                )
            else:
                looking_for = "%{0}%".format(looking_for)
            sigs_to_link_query = db_session.query(Signature).filter(
                Signature.name.ilike(looking_for)
            )
            results = sigs_to_link_query.all()
            for sig_to_link in results:
                crud.link.create(
                    db_session=db_session,
                    obj_in=LinkCreate(
                        v0_type=TargetTypeEnum.alertgroup,
                        v0_id=db_obj.id,
                        v1_type=TargetTypeEnum.signature,
                        v1_id=sig_to_link.id,
                        context=f"Automatically linked from alertgroup subject matching: {looking_for}",
                    ),
                )
        # Finally, add tags and sources if provided
        if obj_in.tags:
            for t in obj_in.tags:
                tag.assign_by_name(db_session, t, TargetTypeEnum.alertgroup,
                    db_obj.id, create=True, audit_logger=audit_logger)
        if obj_in.sources:
            for s in obj_in.sources:
                source.assign_by_name(db_session, s, TargetTypeEnum.alertgroup,
                    db_obj.id, create=True, audit_logger=audit_logger)
        db_session.refresh(db_obj)
        # Log
        if audit_logger is not None:
            audit_logger.log("create", db_obj)
        return db_obj

    def create_with_permissions(
        self,
        db_session: Session,
        *,
        obj_in: Union[AlertGroupCreate, AlertGroupDetailedCreate],
        perm_in: dict[PermissionEnum, list],
        audit_logger=None,
    ) -> AlertGroup:
        """Create an alertgroup given an AlertGroupCreate Object
        First create the alertgroup. Get back the alertgroup ID.
        Next, create the alertgroup schema
        Next, create the alerts, with the given alertgroup ID.
        Fin

        """

        if PermissionEnum.admin in perm_in:
            raise ValueError("Users cannot assign admin permissions")
        db_obj = AlertGroup(
            owner=obj_in.owner,
            tlp=obj_in.tlp,
            view_count=obj_in.view_count,
            first_view=obj_in.first_view,
            message_id=obj_in.message_id,
            subject=obj_in.subject,
        )

        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)

        tt = self.model.target_type_enum()
        # Assign permissions (if applicable)
        if tt:
            # need to import here to avoid circular dependency
            from app.crud import permission, role

            for perm in perm_in:
                new_perm = {
                    "permission": perm,
                    "target_type": tt,
                    "target_id": db_obj.id,
                }
                for r in perm_in[perm]:
                    role_id = r
                    if not isinstance(r, int):
                        role_id = role.get_role_by_name(db_session, r).id
                    new_perm["role_id"] = role_id
                    permission.create(
                        db_session, obj_in=new_perm, audit_logger=audit_logger
                    )

        # Also create the schema and add alerts if detailed create
        if isinstance(obj_in, AlertGroupDetailedCreate):
            schema = None
            if obj_in.alert_schema:
                schema = obj_in.alert_schema
            # Create the schema if one wasn't given
            elif obj_in.alerts:
                schema = self.validate_alerts(obj_in.alerts)
            if schema is not None:
                # We have a valid schema, now let's add it
                for schema_column in schema:
                    schema_column.alertgroup_id = db_obj.id
                    crud.alert_group_schema.create(
                        db_session=db_session, obj_in=schema_column
                    )
                # We've now validated and added the schema, lets add the alerts now
                for alert in obj_in.alerts:
                    if alert.owner is None:
                        alert.owner = obj_in.owner
                    if alert.tlp == TlpEnum.unset:
                        alert.tlp = obj_in.tlp
                    alert.alertgroup_id = db_obj.id
                    crud.alert.create_with_permissions(db_session=db_session, obj_in=alert, perm_in=perm_in)
        self.publish("create", db_obj)
        # Last thing, check to see if the alert group subject is contained in any existing signatures, if so, add links.
        looking_for = re.sub(r"\([^()]*\)", "", obj_in.subject)
        if "*" in looking_for or "_" in looking_for:
            looking_for = looking_for.lstrip().replace("\\", "\\\\")
            looking_for = (
                looking_for.replace("_", "__").replace("*", "%").replace("?", "_")
            )
        else:
            looking_for = looking_for.lstrip()
            looking_for = "%{0}%".format(escape_sql_like(looking_for))
        sigs_to_link_query = db_session.query(Signature).filter(
            Signature.name.ilike(looking_for)
        )
        results = sigs_to_link_query.all()
        for sig_to_link in results:
            crud.link.create(
                db_session=db_session,
                obj_in=LinkCreate(
                    v0_type=TargetTypeEnum.alertgroup,
                    v0_id=db_obj.id,
                    v1_type=TargetTypeEnum.signature,
                    v1_id=sig_to_link.id,
                    context=f"Automatically linked from alertgroup subject matching: {looking_for}",
                ),
            )
        if audit_logger is not None:
            audit_logger.log("create", db_obj)
        return db_obj

    def create_with_owner(
        self,
        db_session: Session,
        *,
        obj_in: Union[AlertGroupCreate, AlertGroupDetailedCreate],
        owner: User,
        audit_logger=None
    ):
        # Create the alertgroup, then give permissions on the alerts
        alertgroup = super().create_with_owner(
            db_session, obj_in=obj_in, owner=owner, audit_logger=audit_logger)
        permission_roles = crud_permission.get_permission_roles(
            db_session, TargetTypeEnum.alertgroup, alertgroup.id)
        if permission_roles:
            for permission in permission_roles:
                for role in permission_roles[permission]:
                    for alert in alertgroup.alerts:
                        new_permission = Permission(
                            role_id=role.id,
                            target_type=TargetTypeEnum.alert,
                            target_id=alert.id,
                            permission=permission,
                        )
                        db_session.add(new_permission)
            db_session.flush()
        return alertgroup

    def add_column(
        self,
        db_session: Session,
        alertgroup_id: int,
        column_name: str,
        values: Dict[str, str] = {},
        audit_logger=None,
    ):
        alertgroup = self.get(db_session, alertgroup_id)
        if not alertgroup:
            raise ValueError("Alertgroup %s not found" % alertgroup_id)
        new_column = crud.alert_group_schema.append_alertgroup_column(
            db_session, column_name, alertgroup_id)
        for alert in alertgroup.alerts:
            new_value = values.get(str(alert.id), "")
            new_alertdata = AlertData(
                schema_key_id=new_column.id, data_value=new_value)
            alert.data_cells[column_name] = new_alertdata
            if audit_logger is not None:
                audit_logger.log("update", {column_name: new_value},
                     thing_type=TargetTypeEnum.alert, thing_pk=alert.id)
        if audit_logger is not None:
            audit_logger.log("update",
                 None,
                 thing_type=TargetTypeEnum.alertgroup,
                 thing_subtype=TargetTypeEnum.alert,
                 thing_pk=alertgroup_id)
        db_session.add(alertgroup)
        db_session.flush()
        db_session.refresh(alertgroup)
        return alertgroup

    def validate_alerts(self, alerts: list[Alert]):
        """Ensure that the alerts have the same schema.

        For every alert, iterate through the AlertData Objects make sure each alert
        has the same schema
        """
        # error = False
        first_schema_keys = None
        schema_create_obj = None
        for alert in alerts:
            if alert.data is not None:
                schema_keys = [a.name for a in alert.data]
                schema_create_obj = [
                    AlertGroupSchemaColumnCreate(
                        schema_key_name=x, schema_key_type=None, schema_key_order=y
                    )
                    for y, x in enumerate(schema_keys)
                ]
                if first_schema_keys is None:
                    first_schema_keys = schema_keys
                else:
                    if (
                        self.are_equal(
                            first_schema_keys,
                            schema_keys,
                            len(first_schema_keys),
                            len(schema_keys),
                        )
                        is True
                    ):
                        pass
                    else:
                        return None
        return schema_create_obj

    def are_equal(self, arr1: list, arr2: list, n: int, m: int) -> bool:
        # If lengths of array are not
        # equal means array are not equal
        if n != m:
            return False
        # Create a defaultdict count to
        # store counts
        count = defaultdict(int)
        # Store the elements of arr1
        # and their counts in the dictionary
        for i in arr1:
            count[i] += 1
        # Traverse through arr2 and compare
        # the elements and its count with
        # the elements of arr1
        for i in arr2:
            # Return false if the element
            # is not in arr2 or if any element
            # appears more no. of times than in arr1
            if count.get(i) is None:
                return False

            elif count[i] == 0:
                return False
            # If element is found, decrement
            # its value in the dictionary
            else:
                count[i] -= 1
        # Return true if both arr1 and
        # arr2 are equal
        return True

    def undelete(
        self,
        db_session: Session,
        target_id: int | None = None,
        existing_data=None,
        keep_ids: bool = True,
        by_user: str | None = None,
        audit_logger=None,
    ):
        # Get data from audits (if present), and restore base alertgroup
        if existing_data is None:
            if target_id is None:
                raise ValueError("Must specify target id to restore")
            query = db_session.query(Audit).filter(
                (Audit.what == "delete")
                & (Audit.thing_type == TargetTypeEnum.alertgroup.value)
                & (Audit.thing_id == target_id)
            )
            if by_user is not None:
                query = query.filter(Audit.username == by_user)
            audit = query.order_by(Audit.when_date.desc()).first()
            if not audit:
                raise ValueError("Target deleted object not found")
            object_data = audit.audit_data
        else:
            object_data = existing_data
        restored_alertgroup = super().undelete(
            db_session=db_session,
            existing_data=object_data,
            keep_ids=keep_ids,
            by_user=by_user,
            audit_logger=audit_logger,
        )
        # Restore all alerts and schemas
        if "alert_schema" in object_data:
            for schema in object_data["alert_schema"]:
                if not keep_ids:
                    schema["alertgroup_id"] = restored_alertgroup.id
                crud.alert_group_schema.undelete(
                    db_session,
                    existing_data=schema,
                    keep_ids=keep_ids,
                    audit_logger=audit_logger,
                )
        if "alerts" in object_data:
            for alert in object_data["alerts"]:
                if not keep_ids:
                    alert["alertgroup_id"] = restored_alertgroup.id
                crud.alert.undelete(
                    db_session,
                    existing_data=alert,
                    keep_ids=keep_ids,
                    audit_logger=audit_logger,
                )
        db_session.flush()
        db_session.refresh(restored_alertgroup)
        return restored_alertgroup

    def increment_view_count(self, db_session: Session, id: int, new_transaction=True):
        alertgroup = db_session.get(AlertGroup, id)
        if alertgroup:
            if new_transaction:
                # This is okay for typical "read" use, since all we've done is
                # a single select of an object
                db_session.commit()
            if alertgroup.view_count == 0:
                alertgroup.first_view = datetime.utcnow()
                alertgroup.view_count = AlertGroup.view_count + 1
            else:
                # Use manual update to avoid changing the "modified" field
                db_session.execute(
                    update(AlertGroup)
                    .where(AlertGroup.id == id)
                    .values(
                        view_count=AlertGroup.view_count + 1,
                        modified=AlertGroup.modified,
                    )
                )
            if new_transaction:
                # Commit as soon as possible to avoid deadlocks
                db_session.commit()
            else:
                db_session.flush()

    def flair_update(
        self,
        db_session: Session,
        alertgroup_id: int,
        alert_results: list[AlertFlairResult],
        audit_logger=None,
    ) -> AlertGroup:
        alertgroup = self.get(db_session, alertgroup_id)

        if alertgroup is not None:

            alert_flair_updates = {
                a.id: a for a in alert_results if a.id in alertgroup.alert_ids
            }
            # Update each alert's flair individually

            for alert_id, alert_results in alert_flair_updates.items():
                crud.alert.flair_update(
                    db_session,
                    alert_id,
                    flair_result=alert_results,
                    audit_logger=audit_logger
                )

                # Also link each entity to the alertgroup
                if alert_results.entities is not None:
                    for entity_type in alert_results.entities:
                        for entity in alert_results.entities[entity_type]:
                            crud.entity.link_entity_by_value(
                                db_session,
                                entity_value=entity,
                                target_type=TargetTypeEnum.alertgroup,
                                target_id=alertgroup_id,
                                entity_type=entity_type,
                                audit_logger=audit_logger,
                            )
            db_session.refresh(alertgroup)
        return alertgroup


alert_group = CRUDAlertGroup(AlertGroup)
