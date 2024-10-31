from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.enums import TargetTypeEnum


class PromotionBase(BaseModel):
    p0_id: Annotated[int, Field(...)]
    p0_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    p1_id: Annotated[int, Field(...)]
    p1_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]


class PromotionCreate(PromotionBase):
    pass


class PromotionUpdate(PromotionBase):
    p0_id: Annotated[int | None, Field(...)] = None
    p0_type: Annotated[TargetTypeEnum | None, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = TargetTypeEnum.none
    p1_id: Annotated[int | None, Field(...)] = None
    p1_type: Annotated[TargetTypeEnum | None, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = TargetTypeEnum.none


class Promotion(PromotionBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()

    model_config = ConfigDict(from_attributes=True)
