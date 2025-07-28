from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, Field


class StatBase(BaseModel):
    year: Annotated[int, Field(...)]
    quarter: Annotated[int, Field(...)]
    month: Annotated[int, Field(...)]
    day_of_week: Annotated[int, Field(...)]
    day: Annotated[int, Field(...)]
    hour: Annotated[int, Field(...)]
    stat_metric: Annotated[str, Field(...)]
    value: Annotated[int, Field(...)]


class StatCreate(StatBase):
    pass


class StatUpdate(StatBase):
    year: Annotated[int | None, Field(...)] = None
    quarter: Annotated[int | None, Field(...)] = None
    month: Annotated[int | None, Field(...)] = None
    day_of_week: Annotated[int | None, Field(...)] = None
    day: Annotated[int | None, Field(...)] = None
    hour: Annotated[int | None, Field(...)] = None
    stat_metric: Annotated[str | None, Field(...)] = None
    value: Annotated[int | None, Field(...)] = None


class Stat(StatBase):
    id: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class StatSearch(BaseModel):
    id: Annotated[str | None, Field(...)] = None
    metric: Annotated[str | None, Field(...)] = None
    value: Annotated[str | None, Field(...)] = None
    year: Annotated[str | None, Field(...)] = None
    quarter: Annotated[str | None, Field(...)] = None
    month: Annotated[str | None, Field(...)] = None
    day: Annotated[str | None, Field(...)] = None
    dow: Annotated[str | None, Field(...)] = None
    hour: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "id" or attr == "value" or attr == "year" or attr == "quarter" or attr == "month" or attr == "day" or attr == "hour":
            return int(value)
        elif attr == "metric" or attr == "dow":
            return value
        else:
            raise AttributeError(f"Unknown attribute {attr}")
