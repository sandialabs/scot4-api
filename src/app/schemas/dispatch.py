from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.enums import StatusEnum, TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase


class DispatchBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum | None, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    status: Annotated[StatusEnum, Field(..., examples=[a.value for a in list(StatusEnum)])] = StatusEnum.open
    subject: Annotated[str | None, Field(...)] = None
    message_id: Annotated[str | None, Field(...)] = None


class DispatchCreate(DispatchBase):
    owner: Annotated[str | None, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class DispatchUpdate(DispatchBase):
    owner: Annotated[str | None, Field(...)] = None


# pretty
class Dispatch(DispatchBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []
    entry_count: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class DispatchSearch(SearchBase):
    owner: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None
    subject: Annotated[str | None, Field(...)] = None
    entry_count: Annotated[str | None, Field(...)] = None
    promoted_to: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "tag" or attr == "source" or attr == "subject" or attr == "promoted_to":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "status":
            return StatusEnum(value)
        elif attr == "entry_count":
            return int(value)
        else:
            return super().type_mapping(attr, value)
