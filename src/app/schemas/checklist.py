from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.enums import TlpEnum
from app.schemas.tag import Tag
from app.schemas.response import SearchBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class ChecklistBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    subject: Annotated[str, Field(...)]
    checklist_data_ver: Annotated[str, Field(...)]
    checklist_data: Annotated[dict | None, Field(...)] = None


class ChecklistCreate(ChecklistBase):
    owner: Annotated[str | None, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class ChecklistUpdate(ChecklistBase):
    owner: Annotated[str | None, Field(...)] = None
    subject: Annotated[str | None, Field(...)] = None


# pretty
class Checklist(ChecklistBase, PopularityVoted, FavoriteLink):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    tags: Annotated[list[Tag] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class ChecklistSearch(SearchBase):
    owner: Annotated[str | None, Field(...)] = None
    subject: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    checklist_data_ver: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "subject" or attr == "tag" or attr == "checklist_data_ver":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        else:
            return super().type_mapping(attr, value)
