import json
from datetime import datetime
from pydantic import BaseModel, field_validator, ConfigDict, Json, Field
from typing import Annotated

from app.schemas.role import Role


class UserBase(BaseModel):
    username: Annotated[str, Field(...)]
    failed_attempts: Annotated[int, Field(...)] = 0
    is_active: Annotated[bool, Field(...)] = True
    pw_hash: Annotated[str | None, Field(...)] = None
    fullname: Annotated[str, Field(...)] = "user"
    email: Annotated[str | None, Field(...)] = None
    preferences: Annotated[Json | None, Field(...)] = None
    is_superuser: Annotated[bool, Field(...)] = False

    @field_validator("preferences", mode="before")
    def convert_data_to_json(cls, v):
        if isinstance(v, (list, dict)):
            return json.dumps(v).encode("utf-8")
        return v


class UserCreate(UserBase):
    password: Annotated[str | None, Field(...)] = None
    roles: Annotated[list[str], Field(...)] = []


class UserUpdate(UserBase):
    username: Annotated[str | None, Field(...)] = None
    password: Annotated[str | None, Field(...)] = None
    failed_attempts: Annotated[int | None, Field(...)] = None
    fullname: Annotated[str | None, Field(...)] = None


# API User
class User(UserBase):
    id: Annotated[int, Field(...)]
    roles: Annotated[list[Role], Field(...)] = []
    last_login: Annotated[datetime | None, Field(...)] = None
    last_activity: Annotated[datetime | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)
