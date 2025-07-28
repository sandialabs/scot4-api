from datetime import datetime
from typing import Any, Annotated
from dateutil import parser

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.enums import TargetTypeEnum


class AppearanceBase(BaseModel):
    when_date: Annotated[datetime, Field(...)]
    target_id: Annotated[int | None, Field(...)] = None
    target_type: Annotated[TargetTypeEnum | None, Field(...)] = TargetTypeEnum.none
    value_id: Annotated[int | None, Field(...)] = None
    value_type: Annotated[str | None, Field(...)] = None
    value_str: Annotated[str | None, Field(...)] = None


class AppearanceCreate(AppearanceBase):
    pass


class AppearanceUpdate(AppearanceBase):
    when_date: Annotated[datetime | SkipJsonSchema[None], Field(...)] = None


# pretty
class Appearance(AppearanceBase):
    id: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class AppearanceSearch(BaseModel):
    id: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    when_date: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    value_str: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    value_type: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    target_type: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    target_id: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "id" or attr == "target_id":
            return int(value)
        elif attr == "when_date":
            return parser.parse(value)
        elif attr == "value_str" or attr == "value_type":
            return value
        elif attr == "target_type":
            # since TargetTypeEnum defaults to None when value is bad
            # check to see if value is within its members first
            if value in TargetTypeEnum.__members__:
                return TargetTypeEnum(value)
            else:
                raise ValueError(f"{value} is not a valid {TargetTypeEnum}")
        else:
            raise AttributeError(f"Unknown attribute {attr}")
