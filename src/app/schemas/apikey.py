from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from .role import RoleNoAuth


class ApiKey(BaseModel):
    key: Annotated[str, Field(...)]
    owner: Annotated[str, Field(...)]
    active: Annotated[bool | None, Field(...)] = True
    roles: Annotated[list[RoleNoAuth] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)
