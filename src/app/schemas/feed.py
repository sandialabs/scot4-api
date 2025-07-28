from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, Json, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema
from dateutil import parser

from app.core.config import settings
from app.enums import TlpEnum
from app.schemas.response import SearchBase, ResultBase
from app.schemas.popularity import PopularityVoted


class FeedBase(BaseModel):
    name: Annotated[str, Field(...)]
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    status: Annotated[str, Field(...)] = "paused"
    type: Annotated[str, Field(...)]
    uri: Annotated[str, Field(...)]
    article_count: Annotated[int, Field(...)] = 0
    promotions_count: Annotated[int, Field(...)] = 0
    data: Annotated[Json | None, Field(...)] = None


class FeedCreate(FeedBase):
    name: Annotated[str, Field(...)] = ""
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME
    type: Annotated[str, Field(...)] = ""
    uri: Annotated[str, Field(...)] = ""


class FeedUpdate(FeedBase):
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    status: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    type: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    uri: Annotated[str | SkipJsonSchema[None], Field(...)] = None


# pretty
class Feed(PopularityVoted, FeedBase, ResultBase):
    last_article: Annotated[datetime, Field(...)]
    last_attempt: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class FeedSearch(SearchBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    status: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    uri: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    type: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    article_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    promotions_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    last_article: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    last_attempt: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "name" or attr == "status" or attr == "uri" or attr == "type":
            return value
        elif attr == "article_count" or attr == "promotions_count":
            return int(value)
        elif attr == "last_article" or attr == "last_attempt":
            return parser.parse(value)
        else:
            return super().type_mapping(attr, value)
