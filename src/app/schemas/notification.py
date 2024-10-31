from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    user_id: Annotated[int, Field(...)]
    message: Annotated[str, Field(...)]
    ack: Annotated[bool, Field(...)]
    ref_id: Annotated[str | None, Field(...)] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(NotificationBase):
    user_id: Annotated[int | None, Field(...)] = None
    message: Annotated[str | None, Field(...)] = None
    ack: Annotated[bool | None, Field(...)] = None
    ref_id: Annotated[str | None, Field(...)] = None


class Notification(NotificationBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()

    model_config = ConfigDict(from_attributes=True)
