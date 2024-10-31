from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.enums import TlpEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase


class FileBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    file_pointer: Annotated[str | None, Field(...)] = None
    filename: Annotated[str | None, Field(...)] = None
    filesize: int | None = None
    sha256: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None
    content_type: Annotated[str | None, Field(...)] = None


class FileCreate(FileBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class FileUpdate(FileBase):
    owner: Annotated[str | None, Field(...)] = None


class File(FileBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class FileSearch(SearchBase):
    owner: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None
    filename: Annotated[str | None, Field(...)] = None
    sha256: Annotated[str | None, Field(...)] = None
    glob: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None
    content_type: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "tag" or attr == "source" or attr == "filename" or attr == "sha256" or attr == "glob" or attr == "description" or attr == "content_type":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        else:
            return super().type_mapping(attr, value)
