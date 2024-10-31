from typing import Annotated
from pydantic import BaseModel, Field
from app.enums import TargetTypeEnum


class FlairedEntity(BaseModel):
    entity_type: Annotated[str, Field(...)]
    entity_value: Annotated[str | int, Field(...)]


class FlairedTarget(BaseModel):
    id: Annotated[int, Field(...)]
    type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]


class FlairResults(BaseModel):
    targets: Annotated[list[FlairedTarget], Field(...)]
    entities: Annotated[list[FlairedEntity], Field(...)]


class AlertFlairResult(BaseModel):
    id: Annotated[int, Field(...)]
    text_data: Annotated[dict | None, Field(...)] = None
    flair_data: Annotated[dict | None, Field(...)] = None
    entities: Annotated[dict | None, Field(...)] = None


class FlairEntryRequest(BaseModel):
    id: Annotated[int, Field(...)]
    type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    targets: Annotated[list[FlairedTarget], Field(...)]
    data: Annotated[str, Field(...)]


class FlairUpdateResult(BaseModel):
    target: Annotated[FlairedTarget, Field(...)]
    text_flaired: Annotated[str | None, Field(...)] = None
    text: Annotated[str | None, Field(...)] = None
    text_plain: Annotated[str | None, Field(...)] = None
    entities: Annotated[dict | None, Field(...)] = None
    alerts: Annotated[list[AlertFlairResult] | None, Field(...)] = None
