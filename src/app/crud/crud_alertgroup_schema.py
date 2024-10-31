from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.alertgroupschema import AlertGroupSchemaKeys
from app.schemas.alertgroupschema import (
    AlertGroupSchemaColumnCreate,
    AlertGroupSchemaColumnUpdate,
)


class CRUDAlertGroupSchema(
    CRUDBase[
        AlertGroupSchemaKeys, AlertGroupSchemaColumnCreate, AlertGroupSchemaColumnUpdate
    ]
):
    def get_alertgroup_schemas(self, db_session: Session, alertgroup_id: int):
        return (
            db_session.query(self.model)
            .filter(self.model.alertgroup_id == alertgroup_id)
            .all()
        )

    def get_alertgroup_schema_map(self, db_session: Session, alertgroup_id: int):
        schema_map = {}
        for schema in self.get_alertgroup_schemas(db_session, alertgroup_id):
            schema_map[schema.schema_key_name] = schema.id
        return schema_map

    def append_alertgroup_column(
        self, db_session: Session, new_column_name: str, alertgroup_id: int
    ):
        schema_map = self.get_alertgroup_schema_map(db_session, alertgroup_id)
        if new_column_name in schema_map:
            raise ValueError("Column %s already exists in this alertgroup"
                             % new_column_name)
        max_column_order = (
            db_session.query(func.max(self.model.schema_key_order))
            .filter(self.model.alertgroup_id == alertgroup_id)
            .first()
        )

        new_column = AlertGroupSchemaColumnCreate(
            schema_key_name=new_column_name,
            schema_key_type=None,
            schema_key_order=max_column_order[0] + 1,
            alertgroup_id=alertgroup_id,
        )
        return self.create(db_session, obj_in=new_column)


alert_group_schema = CRUDAlertGroupSchema(AlertGroupSchemaKeys)
