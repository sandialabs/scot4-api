from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.enums import StatusEnum, TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class IntelBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    status: Annotated[StatusEnum | None, Field(..., examples=[a.value for a in list(StatusEnum)])] = StatusEnum.open
    subject: Annotated[str | None, Field(...)] = None


class IntelCreate(IntelBase):
    owner: Annotated[str | None, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class IntelUpdate(IntelBase):
    owner: Annotated[str | None, Field(...)] = None


class Intel(IntelBase, PopularityVoted, FavoriteLink):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    entry_count: Annotated[int, Field(...)]
    file_count: Annotated[int, Field(...)]
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class IntelSearch(SearchBase):
    owner: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None
    subject: Annotated[str | None, Field(...)] = None
    entry_count: Annotated[str | None, Field(...)] = None
    promoted_to: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "tag" or attr == "source" or attr == "subject" or attr == "promoted_to":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "entry_count":
            return int(value)
        elif attr == "status":
            return StatusEnum(value)
        else:
            return super().type_mapping(attr, value)
