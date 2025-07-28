import json

from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, Json, field_validator, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.enums import EntityStatusEnum, TargetTypeEnum
from app.schemas.entity_class import EntityClass
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase, ResultBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


class EntityAppearanceEntry(BaseModel):
    id: Annotated[int, Field(...)]
    type: Annotated[TargetTypeEnum, Field(...)]
    last_updated: Annotated[datetime, Field(...)]
    subject: Annotated[str | None, Field(...)]
    status: Annotated[str, Field(...)]


class EntityAppearanceEntryAlert(EntityAppearanceEntry):
    alertgroup_id: Annotated[int | None, Field(...)]
    promoted_ids: Annotated[list[int] | None, Field(...)]


a_examples = [
    # Alert example needs to be separate
    [{
        "id": 0,
        "type": "alert",
        "last_updated": "2025-01-01T08:00:00Z",
        "subject": "string",
        "status": "string",
        "alertgroup_id": 1,
        "promoted_ids": [2, 3]
    }]
] + [
    [{
        "id": 0,
        "type": app_type,
        "last_updated": "2025-01-01T08:00:00Z",
        "subject": "string",
        "status": "string"
    }] for app_type in
    ["event", "intel", "product", "incident", "dispatch", "signature", "vuln_feed", "vuln_track"]
]


class EntityAppearancesForFlair(BaseModel):
    alert_appearances: Annotated[list[EntityAppearanceEntryAlert], Field(..., examples=[a_examples[0]])]
    event_appearances: Annotated[list[EntityAppearanceEntry], Field(..., examples=[a_examples[1]])]
    intel_appearances: Annotated[list[EntityAppearanceEntry], Field(..., examples=[a_examples[2]])]
    product_appearances: Annotated[list[EntityAppearanceEntry], Field(..., examples=[a_examples[3]])]
    incident_appearances: Annotated[list[EntityAppearanceEntry], Field(..., examples=[a_examples[4]])]
    dispatch_appearances: Annotated[list[EntityAppearanceEntry], Field(..., examples=[a_examples[5]])]
    signature_appearances: Annotated[list[EntityAppearanceEntry], Field(..., examples=[a_examples[6]])]
    vuln_feed_appearances: Annotated[list[EntityAppearanceEntry], Field(..., examples=[a_examples[7]])]
    vuln_track_appearances: Annotated[list[EntityAppearanceEntry], Field(..., examples=[a_examples[8]])]


class EntityBase(BaseModel):
    status: Annotated[EntityStatusEnum | None, Field(..., examples=[a.value for a in list(EntityStatusEnum)])] = EntityStatusEnum.tracked
    value: Annotated[str | None, Field(...)] = None
    type_id: Annotated[int | None, Field(...)] = None
    data_ver: Annotated[str | None, Field(...)] = None
    data: Annotated[dict | None, Field(..., examples=[{}])] = None


class EntityCreate(EntityBase):
    type_name: Annotated[str | None, Field(...)] = None
    classes: Annotated[list[str], Field(...)] = []


class EntityUpdate(EntityBase):
    pass


# pretty
class Entity(PopularityVoted, FavoriteLink, EntityBase, ResultBase):
    type_name: Annotated[str | None, Field(...)] = None
    classes: Annotated[list[EntityClass], Field(...)] = []
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []
    entity_count: Annotated[int | None, Field(...)] = None
    entry_annotation: Annotated[str | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)


class EntitySearch(SearchBase):
    source: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tag: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    value: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    type_name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    entity_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    status: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    classes: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr in ["source", "tag", "value", "type_name", "classes"]:
            return value
        elif attr == "entity_count":
            return int(value)
        elif attr == "status":
            return EntityStatusEnum(value)
        else:
            return super().type_mapping(attr, value)
