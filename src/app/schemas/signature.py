from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field, Json
from pydantic.json_schema import SkipJsonSchema

from app.core.config import settings
from app.enums import TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase, ResultBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


sigdata_examples = [{
    "signature_body": "signature body",
    "signature_group": ["group1", "group2"],
    "action": ["alert"]
}]


class SignatureBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    latest_revision: Annotated[int | None, Field(...)] = 0
    name: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None
    type: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None
    stats: Annotated[dict | list[dict] | None, Field(...)] = None
    options: Annotated[dict | list[dict] | None, Field(...)] = None
    data_ver: Annotated[str | None, Field(...)] = None
    data: Annotated[dict | list[dict] | SkipJsonSchema[Json] | None, Field(..., examples=sigdata_examples)] = None


class SignatureCreate(SignatureBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class SignatureUpdate(SignatureBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None


class Signature(PopularityVoted, FavoriteLink, SignatureBase, ResultBase):
    entry_count: Annotated[int, Field(...)]
    tags: Annotated[list[Tag], Field(...)] = []
    sources: Annotated[list[Source], Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class SignatureSearch(SearchBase):
    name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    description: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    signature_group: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    type: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tlp: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tag: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    source: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    status: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "name" or attr == "description" or attr == "signature_group" or attr == "type" or attr == "owner" or attr == "tag" or attr == "source" or attr == "status":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        else:
            return super().type_mapping(attr, value)
