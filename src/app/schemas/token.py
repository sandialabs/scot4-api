from pydantic import BaseModel, Field
from typing import Annotated


class Token(BaseModel):
    access_token: Annotated[str, Field(...)]
    token_type: Annotated[str, Field(...)]


class TokenPayload(BaseModel):
    u: Annotated[str | None, Field(...)] = None
    token_roles: Annotated[list[str] | None, Field(...)] = []
