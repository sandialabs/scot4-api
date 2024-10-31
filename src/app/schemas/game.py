from typing import Annotated
from pydantic import BaseModel, Json, ConfigDict, Field


class GameBase(BaseModel):
    name: Annotated[str | None, Field(...)] = None
    tooltip: Annotated[str | None, Field(...)] = None
    parameters: Annotated[Json[dict] | dict | None, Field(...)] = {}


class GameCreate(GameBase):
    pass


class GameUpdate(GameBase):
    pass


class GameResult(BaseModel):
    name: Annotated[str | None, Field(...)] = None
    tooltip: Annotated[str | None, Field(...)] = None
    results: Annotated[Json[dict] | dict | None, Field(...)] = {}


# pretty
class Game(GameBase):
    id: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)
