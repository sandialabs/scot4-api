from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, Json, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema
from app.schemas.response import SearchBase, ResultBase
from app.schemas.popularity import PopularityVoted


class EntityClassLink(BaseModel):
    entity_class_ids: Annotated[list[int | str], Field(...)]


class EntityClassBase(BaseModel):
    display_name: Annotated[str, Field(...)]
    name: Annotated[str, Field(...)]
    icon: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None
    data: Annotated[dict | None, Field(..., examples=[{}])] = None


class EntityClassCreate(EntityClassBase):
    display_name: Annotated[str | None, Field(...)] = ""
    name: Annotated[str | None, Field(...)] = ""


class EntityClassUpdate(EntityClassCreate):
    display_name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    description: Annotated[str | SkipJsonSchema[None], Field(...)] = None


# pretty
class EntityClass(EntityClassBase, ResultBase):

    model_config = ConfigDict(from_attributes=True)


class EntityClassSearch(SearchBase):
    description: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    display_name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    icon: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "description" or attr == "display_name" or attr == "name" or attr == "icon":
            return value

        return super().type_mapping(attr, value)
