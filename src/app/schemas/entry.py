import json

from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, Json, field_validator, ConfigDict, Field

from app.core.config import settings
from app.enums import EntryClassEnum, TargetTypeEnum, TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.utils import sanitize_html
from app.schemas.response import SearchBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class EntryBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    parent_entry_id: Annotated[int | None, Field(...)] = None
    target_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = None
    target_id: Annotated[int | None, Field(...)] = None
    entry_class: Annotated[EntryClassEnum, Field(..., examples=[a.value for a in list(EntryClassEnum)])] = EntryClassEnum.entry

    entry_data_ver: Annotated[str | None, Field(...)] = None
    entry_data: Annotated[Json | None, Field(...)] = None
    parsed: Annotated[bool | None, Field(...)] = False

    @field_validator("entry_data", mode="before")
    def sanitize(cls, v: Json | dict | list[dict] | None):
        if v is not None:
            try:
                v = json.loads(v)
            except (ValueError, TypeError):
                pass

            # Sanitize both the html and flaired html fields
            if isinstance(v, dict):
                if v.get("html") is not None:
                    v['html'] = sanitize_html(v.get("html"))
                if v.get('flaired_html') is not None:
                    v['flaired_html'] = sanitize_html(v.get("flaired_html"))
                v = json.dumps(v).encode("utf-8")
            elif isinstance(v, list):
                for x in v:
                    if x.get("html") is not None:
                        x['html'] = sanitize_html(x.get("html"))
                    if x.get('flaired_html') is not None:
                        x['flaired_html'] = sanitize_html(x.get("flaired_html"))

                v = json.dumps(v).encode("utf-8")

        return v


class EntryCreate(EntryBase):
    owner: Annotated[str | None, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class EntryUpdate(EntryBase):
    owner: Annotated[str | None, Field(...)] = None
    target_type: Annotated[TargetTypeEnum | None, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = TargetTypeEnum.none
    target_id: Annotated[int | None, Field(...)] = None
    parsed: Annotated[bool | None, Field(...)] = None


# pretty
class Entry(EntryBase, PopularityVoted, FavoriteLink):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class EntryWithParent(Entry):
    parent_subject: Annotated[str | None, Field(...)] = None


class EntrySearch(SearchBase):
    owner: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None
    target_type: Annotated[str | None, Field(...)] = None
    target_id: Annotated[str | None, Field(...)] = None
    entry_class: Annotated[str | None, Field(...)] = None
    task_assignee: Annotated[str | None, Field(...)] = None
    task_status: Annotated[str | None, Field(...)] = None
    parent_subject: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "tag" or attr == "source" or attr == "task_assignee" or attr == "task_status" or attr == "parent_subject":
            return value
        elif attr == "target_type":
            # since TargetTypeEnum defaults to None when value is bad
            # check to see if value is within its members first
            if value in TargetTypeEnum.__members__:
                return TargetTypeEnum(value)
            else:
                raise ValueError(f"{value} is not a valid {TargetTypeEnum}")
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "entry_class":
            return EntryClassEnum(value)
        elif attr == "target_id":
            return int(value)
        else:
            return super().type_mapping(attr, value)
