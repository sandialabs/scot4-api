from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Json, ConfigDict, Field

from app.enums import EntityTypeStatusEnum
from app.schemas.response import SearchBase


class EntityTypeBase(BaseModel):
    name: Annotated[str, Field(...)]
    match_order: Annotated[int | None, Field(...)] = None
    status: Annotated[EntityTypeStatusEnum | None, Field(..., examples=[a.value for a in list(EntityTypeStatusEnum)])] = EntityTypeStatusEnum.active
    options: Annotated[Json[dict] | None, Field(...)] = None
    match: Annotated[str | None, Field(...)] = None
    entity_type_data_ver: Annotated[str | None, Field(...)] = None
    entity_type_data: Annotated[Json[dict] | None, Field(...)] = None


class EntityTypeCreate(EntityTypeBase):
    pass


class EntityTypeUpdate(EntityTypeBase):
    name: Annotated[str | None, Field(...)] = None
    match_order: Annotated[int | None, Field(...)] = None


# pretty
class EntityType(EntityTypeBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class EntityTypeSearch(SearchBase):
    pass
