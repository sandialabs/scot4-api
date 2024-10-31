from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.response import SearchBase


class TagBase(BaseModel):
    name: Annotated[str, Field(...)]
    description: Annotated[str | None, Field(...)] = None
    type_name: Annotated[str | None, Field(...)] = None
    type_description: Annotated[str | None, Field(...)] = None

    # Tag names are always lowercase
    @field_validator("name")
    def ensure_lowercase(cls, v: str):
        return v.lower()


class TagCreate(TagBase):
    tag_type_id: Annotated[int | None, Field(...)] = 1


class TagUpdate(TagBase):
    name: Annotated[str | None, Field(...)] = None


class Tag(TagBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()

    model_config = ConfigDict(from_attributes=True)


class TagSearch(SearchBase):
    name: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "name" or attr == "description":
            return value
        else:
            return super().type_mapping(attr, value)
