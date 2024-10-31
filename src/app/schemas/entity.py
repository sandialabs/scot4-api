import json

from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, Json, field_validator, ConfigDict, Field

from app.enums import EntityStatusEnum
from app.schemas.entity_class import EntityClass
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase


class EntityAppearancesForFlair(BaseModel):
    alert_appearances: Annotated[list[dict], Field(...)]
    event_appearances: Annotated[list[dict], Field(...)]
    intel_appearances: Annotated[list[dict], Field(...)]
    product_appearances: Annotated[list[dict], Field(...)]
    incident_appearances: Annotated[list[dict], Field(...)]
    dispatch_appearances: Annotated[list[dict], Field(...)]
    signature_appearances: Annotated[list[dict], Field(...)]
    vuln_feed_appearances: Annotated[list[dict], Field(...)]
    vuln_track_appearances: Annotated[list[dict], Field(...)]


class EntityBase(BaseModel):
    status: Annotated[EntityStatusEnum | None, Field(..., examples=[a.value for a in list(EntityStatusEnum)])] = EntityStatusEnum.tracked
    value: Annotated[str | None, Field(...)] = None
    classes: Annotated[list[EntityClass] | None, Field(...)] = None
    type_name: Annotated[str | None, Field(...)] = None
    type_id: Annotated[int | None, Field(...)] = None
    data_ver: Annotated[str | None, Field(...)] = None
    data: Annotated[Json | None, Field(...)] = None

    @field_validator("data", mode="before")
    def convert_data_to_json(cls, v):
        if isinstance(v, (list, dict)):
            return json.dumps(v).encode("utf-8")
        return v


class EntityCreate(EntityBase):
    pass


class EntityUpdate(EntityBase):
    pass


# pretty
class Entity(EntityBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []
    entity_count: Annotated[int | None, Field(...)] = None
    entry_annotation: Annotated[str | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)


class EntitySearch(SearchBase):
    source: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    value: Annotated[str | None, Field(...)] = None
    type_name: Annotated[str | None, Field(...)] = None
    entity_count: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "source" or attr == "tag" or attr == "value" or attr == "type_name":
            return value
        elif attr == "entity_count":
            return int(value)
        elif attr == "status":
            return EntityStatusEnum(value)
        else:
            return super().type_mapping(attr, value)
