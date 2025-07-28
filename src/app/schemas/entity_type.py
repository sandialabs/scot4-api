from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Json, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.enums import EntityTypeStatusEnum
from app.schemas.response import SearchBase, ResultBase


class EntityTypeBase(BaseModel):
    name: Annotated[str, Field(...)]
    match_order: Annotated[int | None, Field(...)] = None
    status: Annotated[EntityTypeStatusEnum, Field(..., examples=[a.value for a in list(EntityTypeStatusEnum)])] = EntityTypeStatusEnum.active
    options: Annotated[Json[dict] | None, Field(..., examples=[{}])] = None
    match: Annotated[str | None, Field(...)] = None
    entity_type_data_ver: Annotated[str | None, Field(...)] = None
    entity_type_data: Annotated[dict | None, Field(..., examples=[{}])] = None


class EntityTypeCreate(EntityTypeBase):
    pass


class EntityTypeUpdate(EntityTypeBase):
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None


# pretty
class EntityType(EntityTypeBase, ResultBase):

    model_config = ConfigDict(from_attributes=True)


class EntityTypeSearch(SearchBase):
    pass
