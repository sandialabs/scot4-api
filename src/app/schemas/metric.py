from typing import Annotated
from pydantic import BaseModel, Json, ConfigDict, Field


class MetricBase(BaseModel):
    name: Annotated[str | None, Field(...)] = None
    tooltip: Annotated[str | None, Field(...)] = None
    parameters: Annotated[Json[dict] | dict | None, Field(...)] = {}


class MetricCreate(MetricBase):
    pass


class MetricUpdate(MetricBase):
    pass


class MetricResult(BaseModel):
    name: Annotated[str | None, Field(...)] = None
    tooltip: Annotated[str | None, Field(...)] = None
    results: Annotated[Json[dict] | dict | None, Field(...)] = {}


# pretty
class Metric(MetricBase):
    id: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)