from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, field_validator, ConfigDict, Field

from app.schemas.response import SearchBase


class SourceBase(BaseModel):
    name: Annotated[str, Field(...)]
    description: Annotated[str | None, Field(...)] = None

    # Source names are always lowercase
    @field_validator("name")
    def ensure_lowercase(cls, v: str):
        return v.lower()


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SourceCreate):
    name: Annotated[str | None, Field(...)] = None


# pretty
class Source(SourceBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()

    model_config = ConfigDict(from_attributes=True)


class SourceSearch(SearchBase):
    name: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "name" or attr == "description":
            return value
        else:
            return super().type_mapping(attr, value)
