from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.enums import TargetTypeEnum


class LinkBase(BaseModel):
    v0_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    v0_id: Annotated[int, Field(...)]
    v1_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    v1_id: Annotated[int, Field(...)]
    weight: Annotated[int | None, Field(...)] = None
    context: Annotated[str | None, Field(...)] = None


class LinkCreate(LinkBase):
    pass


class LinkUpdate(LinkBase):
    v0_type: Annotated[TargetTypeEnum | None, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = TargetTypeEnum.none
    v0_id: Annotated[int | None, Field(...)] = None
    v1_type: Annotated[TargetTypeEnum | None, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = TargetTypeEnum.none
    v1_id: Annotated[int | None, Field(...)] = None


# pretty
class Link(LinkBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = None
    modified: Annotated[datetime | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)


class LinkSearch(BaseModel):
    v0_type: Annotated[str | None, Field(...)] = None
    v0_id: Annotated[str | None, Field(...)] = None
    v1_id: Annotated[str | None, Field(...)] = None
    v1_type: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "v0_id" or attr == "v1_id":
            return int(value)
        elif attr == "v0_type" or attr == "v1_type":
            # since TargetTypeEnum defaults to None when value is bad
            # check to see if value is within its members first
            if value in TargetTypeEnum.__members__:
                return TargetTypeEnum(value)
            else:
                raise ValueError(f"{value} is not a valid {TargetTypeEnum}")
        else:
            raise AttributeError(f"Unknown attribute {attr}")
