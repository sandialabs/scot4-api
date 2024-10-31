from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class AlertGroupSchemaColumnBase(BaseModel):
    alertgroup_id: Annotated[int, Field(...)]
    schema_key_name: Annotated[str, Field(...)]
    schema_key_type: Annotated[str | None, Field(...)] = ""
    schema_key_order: Annotated[int | None, Field(...)] = 0

    model_config = ConfigDict(from_attributes=True)


class AlertGroupSchemaColumnCreate(AlertGroupSchemaColumnBase):
    alertgroup_id: Annotated[int | None, Field(...)] = None


class AlertGroupSchemaColumnUpdate(AlertGroupSchemaColumnBase):
    pass


class AlertGroupSchemaColumn(AlertGroupSchemaColumnBase):
    id: Annotated[int, Field(...)]
