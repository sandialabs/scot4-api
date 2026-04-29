from typing import Any, Annotated
from pydantic import BaseModel, field_validator, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.schemas.response import SearchBase, ResultBase
from app.enums import TargetTypeEnum


class SourceBase(BaseModel):
    name: Annotated[str, Field(...)]
    description: Annotated[str | None, Field(...)] = None

    # Source names are always lowercase removes and leading or
    # trailing whitespace and replaces any spaces with underscores
    @field_validator("name")
    def check_name(cls, v: str):
        return v.lower().strip().replace(" ", "_")


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SourceCreate):
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None


# pretty
class Source(SourceBase, ResultBase):
    link_count: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class SourceSearch(SearchBase):
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    description: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "name" or attr == "description":
            return value
        else:
            return super().type_mapping(attr, value)


class LinkSources(BaseModel):
    target_type: Annotated[TargetTypeEnum, Field(...)]
    target_id: Annotated[int, Field(...)]
    items: Annotated[list[Source], Field(...)] = []
