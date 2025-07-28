from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.core.config import settings
from app.enums import TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase, ResultBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class ProductBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    subject: Annotated[str | None, Field(...)] = None


class ProductCreate(ProductBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class ProductUpdate(ProductBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None


# pretty
class Product(PopularityVoted, FavoriteLink, ProductBase, ResultBase):
    entry_count: Annotated[int, Field(...)]
    file_count: Annotated[int, Field(...)]
    tags: Annotated[list[Tag], Field(...)] = []
    sources: Annotated[list[Source], Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class ProductSearch(SearchBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tlp: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tag: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    source: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    subject: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    entry_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    promoted_from: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "tag" or attr == "source" or attr == "subject" or attr == "promoted_from":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "entry_count":
            return int(value)
        else:
            return super().type_mapping(attr, value)
