from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.enums import RemoteFlairStatusEnum


class RemoteFlairBase(BaseModel):
    md5: Annotated[str, Field(...)]
    uri: Annotated[str, Field(...)]
    status: Annotated[RemoteFlairStatusEnum, Field(..., examples=[a.value for a in list(RemoteFlairStatusEnum)])]
    results: Annotated[dict | None, Field(...)] = None


class RemoteFlairCreate(RemoteFlairBase):
    md5: Annotated[str | None, Field(...)] = None
    uri: Annotated[str, Field(...)]
    html: Annotated[str, Field(...)]
    status: Annotated[RemoteFlairStatusEnum | None, Field(..., examples=[a.value for a in list(RemoteFlairStatusEnum)])] = RemoteFlairStatusEnum.processing


class RemoteFlairUpdate(RemoteFlairBase):
    md5: Annotated[str | None, Field(...)] = None
    uri: Annotated[str | None, Field(...)] = None
    html: Annotated[str | None, Field(...)] = None
    status: Annotated[RemoteFlairStatusEnum | None, Field(...)] = None


# pretty
class RemoteFlair(RemoteFlairBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)
