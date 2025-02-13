from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, Json, ConfigDict, Field
from dateutil import parser

from app.core.config import settings
from app.enums import TlpEnum
from app.schemas.response import SearchBase
from app.schemas.popularity import PopularityVoted


class FeedBase(BaseModel):
    name: Annotated[str, Field(...)]
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    status: Annotated[str | None, Field(...)] = "paused"
    type: Annotated[str, Field(...)]
    uri: Annotated[str, Field(...)]
    article_count: Annotated[int | None, Field(...)] = 0
    promotions_count: Annotated[int | None, Field(...)] = 0
    data: Annotated[Json | None, Field(...)] = None


class FeedCreate(FeedBase):
    name: Annotated[str | None, Field(...)] = ""
    owner: Annotated[str | None, Field(...)] = settings.FIRST_SUPERUSER_USERNAME
    type: Annotated[str | None, Field(...)] = ""
    uri: Annotated[str | None, Field(...)] = ""


class FeedUpdate(FeedBase):
    name: Annotated[str | None, Field(...)] = None
    owner: Annotated[str | None, Field(...)] = None
    tlp: Annotated[TlpEnum | None, Field(..., examples=[a.value for a in list(TlpEnum)])] = None
    status: Annotated[str | None, Field(...)] = None
    type: Annotated[str | None, Field(...)] = None
    uri: Annotated[str | None, Field(...)] = None


# pretty
class Feed(FeedBase, PopularityVoted):
    id: Annotated[int, Field(...)]
    last_article: Annotated[datetime, Field(...)]
    last_attempt: Annotated[datetime, Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class FeedSearch(SearchBase):
    owner: Annotated[str | None, Field(...)] = None
    name: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None
    uri: Annotated[str | None, Field(...)] = None
    type: Annotated[str | None, Field(...)] = None
    article_count: Annotated[str | None, Field(...)] = None
    promotions_count: Annotated[str | None, Field(...)] = None
    last_article: Annotated[str | None, Field(...)] = None
    last_attempt: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "name" or attr == "status" or attr == "uri" or attr == "type":
            return value
        elif attr == "article_count" or attr == "promotions_count":
            return int(value)
        elif attr == "last_article" or attr == "last_attempt":
            return parser.parse(value)
        else:
            return super().type_mapping(attr, value)
