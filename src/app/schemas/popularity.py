from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from app.core.config import settings
from app.enums import PopularityMetricEnum, TargetTypeEnum
from app.schemas.response import ResultBase


class PopularityBase(BaseModel):
    target_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    target_id: Annotated[int, Field(...)]
    metric_type: Annotated[PopularityMetricEnum, Field(..., examples=[a.value for a in list(PopularityMetricEnum)])]
    owner_id: Annotated[int, Field(...)]


class PopularityCreate(PopularityBase):
    pass


class PopularityUpdate(BaseModel):
    metric_type: Annotated[PopularityMetricEnum, Field(..., examples=[a.value for a in list(PopularityMetricEnum)])]


# pretty
class Popularity(PopularityBase, ResultBase):

    model_config = ConfigDict(from_attributes=True)


# Mixin to denote that a schema includes popularity stuff
class PopularityVoted(BaseModel):
    popularity_count: Annotated[int, Field(...)]
    popularity_voted: Annotated[PopularityMetricEnum | None, Field(...)]

    # Wrapper function to move the properties of the Popularity mixin to the end of the schema
    # Makes the auto-documentation look prettier
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        if hasattr(super(), "__get_pydantic_json_schema__"):
            json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        else:
            json_schema = handler(core_schema)
            json_schema = handler.resolve_ref_schema(json_schema)
        props = json_schema.get("properties", {})
        for field in PopularityVoted.model_fields:
            val = props.pop(field, None)
            if val is not None:
                props[field] = val
        return json_schema
