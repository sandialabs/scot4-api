from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, field_validator, ValidationInfo, ConfigDict, Field


class HandlerBase(BaseModel):
    start_date: Annotated[datetime, Field(...)]
    end_date: Annotated[datetime, Field(...)]
    username: Annotated[str, Field(...)]
    position: Annotated[str | None, Field(...)] = None

    @field_validator("end_date")
    def check_date_order(cls, v, info: ValidationInfo):
        if info.data.get("start_date") and v < info.data.get("start_date"):
            raise ValueError("end_date must be after start_date")
        return v


class HandlerCreate(HandlerBase):
    pass


class HandlerUpdate(HandlerBase):
    start_date: Annotated[datetime | None, Field(...)] = None
    end_date: Annotated[datetime | None, Field(...)] = None
    username: Annotated[str | None, Field(...)] = None


# pretty
class Handler(HandlerBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)
