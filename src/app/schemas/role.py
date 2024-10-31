from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.setting import AuthSettings


class RoleBase(BaseModel):
    name: Annotated[str, Field(...)]
    description: Annotated[str | None, Field(...)] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    name: Annotated[str | None, Field(...)] = None


# pretty
class Role(RoleBase):
    id: Annotated[int, Field(...)]
    auth_methods: Annotated[list[AuthSettings], Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)
