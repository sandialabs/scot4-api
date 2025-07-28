from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.enums import RemoteFlairStatusEnum, RemoteFlairSourceEnum


class RemoteFlairBase(BaseModel):
    md5: Annotated[str, Field(...)]
    uri: Annotated[str, Field(...)]
    status: Annotated[RemoteFlairStatusEnum, Field(..., examples=[a.value for a in list(RemoteFlairStatusEnum)])]
    source: Annotated[RemoteFlairSourceEnum, Field(..., examples=[a.value for a in list(RemoteFlairSourceEnum)])]
    results: Annotated[dict | None, Field(...)] = None


class RemoteFlairCreate(RemoteFlairBase):
    md5: Annotated[str | None, Field(...)] = None
    uri: Annotated[str, Field(...)]
    data: Annotated[str, Field(...)]
    status: Annotated[RemoteFlairStatusEnum | None, Field(..., examples=[a.value for a in list(RemoteFlairStatusEnum)])] = RemoteFlairStatusEnum.processing
    source: Annotated[RemoteFlairSourceEnum, Field(..., examples=[a.value for a in list(RemoteFlairSourceEnum)])]


class RemoteFlairUpdate(RemoteFlairBase):
    md5: Annotated[str | None, Field(...)] = None
    uri: Annotated[str | None, Field(...)] = None
    data: Annotated[str | None, Field(...)] = None
    status: Annotated[RemoteFlairStatusEnum | None, Field(..., examples=[a.value for a in list(RemoteFlairStatusEnum)])] = None
    source: Annotated[RemoteFlairSourceEnum, Field(..., examples=[a.value for a in list(RemoteFlairSourceEnum)])] = None


# pretty
class RemoteFlair(RemoteFlairBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)
