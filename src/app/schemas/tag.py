from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic.json_schema import SkipJsonSchema

from app.schemas.response import SearchBase, ResultBase
from app.enums import TargetTypeEnum


class TagBase(BaseModel):
    name: Annotated[str, Field(...)]
    description: Annotated[str | None, Field(...)] = None

    # Tag names are always lowercase
    @field_validator("name")
    def ensure_lowercase(cls, v: str):
        return v.lower()


class TagCreate(TagBase):
    tag_type_id: Annotated[int | None, Field(...)] = None


class TagUpdate(TagBase):
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None


class Tag(TagBase, ResultBase):
    link_count: Annotated[int, Field(...)]
    type_name: Annotated[str | None, Field(...)] = None
    type_description: Annotated[str | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)


class TagSearch(SearchBase):
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    description: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "name" or attr == "description":
            return value
        else:
            return super().type_mapping(attr, value)


class LinkTags(BaseModel):
    target_type: Annotated[TargetTypeEnum, Field(...)]
    target_id: Annotated[int, Field(...)]
    items: Annotated[list[Tag], Field(...)] = []
