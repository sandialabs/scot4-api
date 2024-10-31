from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class FeedTypeBase(BaseModel):
    type: Annotated[str, Field(...)]


class FeedTypeCreate(FeedTypeBase):
    pass


class FeedTypeUpdate(FeedTypeBase):
    type: Annotated[str | None, Field(...)] = None


# pretty
class FeedType(FeedTypeBase):
    type: Annotated[str, Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)
