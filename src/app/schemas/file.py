from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.core.config import settings
from app.enums import TlpEnum, AlfEnum
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase, ResultBase


class FileBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    alf: Annotated[AlfEnum, Field(..., examples=[a.value for a in list(AlfEnum)])] = AlfEnum.unset
    filename: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None


# Contains immutable fields that must be set only once, at creation
class FileBaseImmutable(FileBase):
    file_pointer: Annotated[str, Field(...)] = ""
    filesize: int | None = None
    sha256: Annotated[str | None, Field(...)] = None
    content_type: Annotated[str | None, Field(...)] = None


class FileCreate(FileBaseImmutable):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class FileUpdate(FileBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None


class File(FileBaseImmutable, ResultBase):
    tags: Annotated[list[Tag], Field(...)] = []
    sources: Annotated[list[Source], Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class FileSearch(SearchBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tlp: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    alf: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tag: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    source: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    filename: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    sha256: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    glob: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    description: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    content_type: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "owner" or attr == "tag" or attr == "source" or attr == "filename" or attr == "sha256" or attr == "glob" or attr == "description" or attr == "content_type":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "alf":
            return AlfEnum(value)
        else:
            return super().type_mapping(attr, value)
