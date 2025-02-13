import json

from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, Json, field_validator, ConfigDict, Field

from app.core.config import settings
from app.enums import StatusEnum, TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class IncidentBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    occurred_date: Annotated[datetime | None, Field(...)] = None
    discovered_date: Annotated[datetime | None, Field(...)] = None
    reported_date: Annotated[datetime | None, Field(...)] = None
    status: Annotated[StatusEnum | None, Field(..., examples=[a.value for a in list(StatusEnum)])] = StatusEnum.open
    subject: Annotated[str | None, Field(...)] = None
    data_ver: Annotated[str | None, Field(...)] = "incident_v2"
    data: Annotated[Json | None, Field(...)] = {}
    view_count: Annotated[int | None, Field(...)] = None

    @field_validator("data", mode="before")
    def convert_data_to_json(cls, v):
        if isinstance(v, (list, dict)):
            return json.dumps(v).encode("utf-8")
        return v


class IncidentCreate(IncidentBase):
    owner: Annotated[str | None, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class IncidentUpdate(IncidentBase):
    owner: Annotated[str | None, Field(...)] = None
    occurred_date: Annotated[datetime | None, Field(...)] = None
    discovered_date: Annotated[datetime | None, Field(...)] = None
    reported_date: Annotated[datetime | None, Field(...)] = None


class Incident(IncidentBase, PopularityVoted, FavoriteLink):
    id: Annotated[int, Field(...)]
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    entry_count: Annotated[int, Field(...)]
    file_count: Annotated[int, Field(...)]
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class IncidentSearch(SearchBase):
    owner: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None
    subject: Annotated[str | None, Field(...)] = None
    view_count: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None
    entry_count: Annotated[str | None, Field(...)] = None
    promoted_from: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "tag" or attr == "source" or attr == "subject" or attr == "promoted_from":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "view_count" or attr == "entry_count":
            return int(value)
        elif attr == "status":
            return StatusEnum(value)
        else:
            return super().type_mapping(attr, value)
