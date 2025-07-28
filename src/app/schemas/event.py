from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.enums import StatusEnum, TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.core.config import settings
from app.schemas.response import SearchBase, ResultBase
from app.schemas.promotion import Promotion
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class EventBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    status: Annotated[StatusEnum, Field(..., examples=[a.value for a in list(StatusEnum)])] = StatusEnum.open
    subject: Annotated[str | None, Field(...)] = None
    view_count: Annotated[int, Field(...)] = 0
    message_id: Annotated[str | None, Field(...)] = None


class EventCreate(EventBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class EventUpdate(EventBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None


# pretty
class Event(PopularityVoted, FavoriteLink, EventBase, ResultBase):
    entry_count: Annotated[int, Field(...)]
    file_count: Annotated[int, Field(...)]
    tags: Annotated[list[Tag], Field(...)] = []
    sources: Annotated[list[Source], Field(...)] = []
    promoted_to_targets: Annotated[list[Promotion], Field(...)] = []
    promoted_from_sources: Annotated[list[Promotion], Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class EventSearch(SearchBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tlp: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tag: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    source: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    subject: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    view_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    status: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    entry_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    promoted_to: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "tag" or attr == "source" or attr == "subject" or attr == "promoted_to":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "view_count" or attr == "entry_count":
            return int(value)
        elif attr == "status":
            return StatusEnum(value)
        else:
            return super().type_mapping(attr, value)
