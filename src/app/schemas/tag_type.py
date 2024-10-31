from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class TagTypeBase(BaseModel):
    name: Annotated[str, Field(...)]
    description: Annotated[str | None, Field(...)] = None


class TagTypeCreate(TagTypeBase):
    pass


class TagTypeUpdate(TagTypeBase):
    name: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None


class TagType(TagTypeBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)
