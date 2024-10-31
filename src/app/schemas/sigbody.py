from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase


class SigbodyBase(BaseModel):
    revision: Annotated[int | None, Field(...)] = None
    body: Annotated[str | None, Field(...)] = None
    body64: Annotated[str | None, Field(...)] = None
    signature_id: Annotated[int | None, Field(...)] = None


class SigbodyCreate(SigbodyBase):
    pass


class SigbodyUpdate(SigbodyCreate):
    pass


# pretty
class Sigbody(SigbodyBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class SigbodySearch(SearchBase):
    tag: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "tag" or attr == "source":
            return value
        else:
            return super().type_mapping(attr, value)
