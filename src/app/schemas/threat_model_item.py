from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, Json, ConfigDict, Field

from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase


class ThreatModelItemBase(BaseModel):
    title: Annotated[str, Field()]
    type: Annotated[str, Field(...)]
    description: Annotated[str | None, Field(...)] = None
    data: Annotated[Json | dict | list[dict], Field(...)]


class ThreatModelItemCreate(ThreatModelItemBase):
    pass


class ThreatModelItemUpdate(ThreatModelItemBase):
    pass


class ThreatModelItem(ThreatModelItemBase):
    id: Annotated[int, Field(...)]
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class ThreatModelItemSearch(SearchBase):
    title: Annotated[str | None, Field(...)] = None
    type: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "title" or attr == "type" or attr == "tag" or attr == "source":
            return value
        else:
            return super().type_mapping(attr, value)
