from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema
from app.enums import PriorityEnum, TargetTypeEnum
from app.schemas.response import ResultBase


class NotificationBase(BaseModel):
    user_id: Annotated[int | None, Field(...)]
    message: Annotated[str, Field(...)]
    ack: Annotated[bool, Field(...)] = False
    priority: Annotated[PriorityEnum, Field(..., examples=[a.value for a in list(PriorityEnum)])] = PriorityEnum.low
    expires: Annotated[datetime | None, Field(...)] = None
    ref_id: Annotated[str | None, Field(...)] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationAck(BaseModel):
    notification_ids: Annotated[list[int], Field(...)]


class NotificationSubscribe(BaseModel):
    target_type: TargetTypeEnum
    target_id: int


class NotificationBroadcast(BaseModel):
    message: Annotated[str, Field(...)]
    priority: Annotated[PriorityEnum, Field(..., examples=[a.value for a in list(PriorityEnum)])] = PriorityEnum.medium
    expires: Annotated[datetime | None, Field(...)] = None


class NotificationUpdate(NotificationBase):
    user_id: Annotated[int | None, Field(...)] = None
    message: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    ack: Annotated[bool | SkipJsonSchema[None], Field(...)] = None
    priority: Annotated[PriorityEnum | SkipJsonSchema[None], Field(..., examples=[a.value for a in list(PriorityEnum)])] = None


class Notification(NotificationBase, ResultBase):

    model_config = ConfigDict(from_attributes=True)
