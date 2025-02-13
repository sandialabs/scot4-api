from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, Json, ConfigDict, Field

from app.core.config import settings
from app.enums import TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class SignatureBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    latest_revision: Annotated[int | None, Field(...)] = 0
    name: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None
    type: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None
    stats: Annotated[Json | dict | list[dict] | None, Field(...)] = None
    options: Annotated[Json | dict | list[dict] | None, Field(...)] = None
    data_ver: Annotated[str | None, Field(...)] = None
    data: Annotated[Json | dict | list[dict] | None, Field(...)] = None


class SignatureCreate(SignatureBase):
    owner: Annotated[str | None, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class SignatureUpdate(SignatureBase):
    owner: Annotated[str | None, Field(...)] = None


class Signature(SignatureBase, PopularityVoted, FavoriteLink):
    id: Annotated[int, Field(...)]
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    entry_count: Annotated[int, Field(...)]
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class SignatureSearch(SearchBase):
    name: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None
    signature_group: Annotated[str | None, Field(...)] = None
    type: Annotated[str | None, Field(...)] = None
    owner: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "name" or attr == "description" or attr == "signature_group" or attr == "type" or attr == "owner" or attr == "tag" or attr == "source" or attr == "status":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        else:
            return super().type_mapping(attr, value)
