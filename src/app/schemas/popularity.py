from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from app.core.config import settings
from app.enums import PopularityMetricEnum, TargetTypeEnum


class PopularityBase(BaseModel):
    target_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    target_id: Annotated[int, Field(...)]
    metric_type: Annotated[PopularityMetricEnum, Field(..., examples=[a.value for a in list(PopularityMetricEnum)])]
    owner_id: Annotated[int, Field(...)]


class PopularityCreate(PopularityBase):
    owner_id: Annotated[int, Field(...)]


class PopularityUpdate(BaseModel):
    metric_type: Annotated[PopularityMetricEnum, Field(..., examples=[a.value for a in list(PopularityMetricEnum)])]


# pretty
class Popularity(PopularityBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime, Field(...)] = datetime.now()
    modified: Annotated[datetime, Field(...)] = datetime.now()

    model_config = ConfigDict(from_attributes=True)


class PopularityVoted(BaseModel):
    popularity_count: Annotated[int | None, Field(...)] = 0
    popularity_voted: Annotated[PopularityMetricEnum | None, Field(...)] = None