from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.setting import AuthSettings
from app.schemas.response import ResultBase


class RoleBase(BaseModel):
    name: Annotated[str, Field(...)]
    description: Annotated[str | None, Field(...)] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    name: Annotated[str, Field(...)] = None


# pretty
class Role(RoleBase, ResultBase):
    auth_methods: Annotated[list[AuthSettings], Field(...)]

    model_config = ConfigDict(from_attributes=True)
