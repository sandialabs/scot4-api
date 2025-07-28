from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema
from dateutil import parser

from app.enums import TargetTypeEnum, SpecialMetricEnum
from app.schemas.response import SearchBase, ResultBase


class SpecialMetricBase(BaseModel):
    target_id: Annotated[int, Field(...)]
    target_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    metric_type: Annotated[SpecialMetricEnum, Field(..., examples=[a.value for a in list(SpecialMetricEnum)])]
    start_time: Annotated[datetime, Field(...)]
    end_time: Annotated[datetime, Field(...)]


class SpecialMetricCreate(SpecialMetricBase):
    pass


class SpecialMetricUpdate(SpecialMetricBase):
    target_id: Annotated[int, Field(...)] = None
    target_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = TargetTypeEnum.none
    metric_type: Annotated[SpecialMetricEnum, Field(..., examples=[a.value for a in list(SpecialMetricEnum)])] = None
    start_time: Annotated[datetime, Field(...)] = None
    end_time: Annotated[datetime, Field(...)] = None


# pretty
class SpecialMetric(SpecialMetricBase, ResultBase):

    model_config = ConfigDict(from_attributes=True)


class SpecialMetricSearch(SearchBase):
    target_id: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    target_type: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    metric_type: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    start_time: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    end_time: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "target_id":
            return int(value)
        elif attr == "target_type":
            return TargetTypeEnum(value)
        elif attr == "metric_type":
            return SpecialMetricEnum(value)
        elif attr == "start_time" or attr == "end_time":
            return parser.parse(value)
        else:
            return super().type_mapping(attr, value)
