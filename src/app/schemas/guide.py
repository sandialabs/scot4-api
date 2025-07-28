from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, Json, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.core.config import settings
from app.enums import GuideStatusEnum, TlpEnum
from app.schemas.response import SearchBase, ResultBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class GuideBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    subject: Annotated[str | None, Field(...)] = None
    status: Annotated[GuideStatusEnum | None, Field(..., examples=[a.value for a in list(GuideStatusEnum)])] = GuideStatusEnum.current
    application: Annotated[dict | None, Field(..., examples=[{}])] = None
    data_ver: Annotated[str | None, Field(...)] = None
    data: Annotated[dict | None, Field(..., examples=[{}])] = None


class GuideCreate(GuideBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class GuideUpdate(GuideBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset


# pretty
class Guide(PopularityVoted, FavoriteLink, GuideBase, ResultBase):
    entry_count: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class GuideSearch(SearchBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tlp: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    subject: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    status: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    entry_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "subject":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "status":
            return GuideStatusEnum(value)
        elif attr == "entry_count":
            return int(value)
        else:
            return super().type_mapping(attr, value)
