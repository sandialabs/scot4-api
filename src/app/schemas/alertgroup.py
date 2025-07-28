from datetime import datetime
from dateutil import parser
from typing import Any, Annotated

from pydantic import BaseModel, field_validator, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

from app.enums import TlpEnum, StatusEnum
from app.core.config import settings
from app.schemas.alert import AlertCreate
from app.schemas.alertgroupschema import AlertGroupSchemaColumnCreate
from app.schemas.response import SearchBase, ResultBase
from app.schemas.tag import Tag
from app.schemas.source import Source
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink
from app.utils import is_bool


class AlertGroupBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    view_count: Annotated[int, Field(...)] = 0
    first_view: Annotated[datetime | None, Field(...)] = None
    message_id: Annotated[str | None, Field(...)] = None
    back_refs: Annotated[str | None, Field(...)] = None
    subject: Annotated[str | None, Field(...)] = None

    model_config = ConfigDict(
        use_enum_values=True,
    )


alert_examples = [
    [{"data": {"number_field": "1", "string_field": "value1"}},
     {"data": {"number_field": "2", "string_field": "value2"}}]
]
alert_schema_examples = [
    [{"schema_key_name": "number_field", "schema_key_type": "number", "schema_key_order": 0},
     {"schema_key_name": "string_field", "schema_key_type": "string", "schema_key_order": 1}]
]


class AlertGroupDetailedCreate(AlertGroupBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME
    alert_schema: Annotated[list[AlertGroupSchemaColumnCreate] | None, Field(..., examples=alert_schema_examples)] = None
    alerts: Annotated[list[AlertCreate], Field(..., examples=alert_examples)] = []
    sources: Annotated[list[str], Field(..., examples=[["sourcename"]])] = []
    tags: Annotated[list[str], Field(..., examples=[["tagname"]])] = []

    model_config = ConfigDict(
        use_enum_values=True,
    )


class AlertGroupCreate(AlertGroupBase):
    sources: Annotated[list[str], Field(..., examples=[["sourcename"]])] = []
    tags: Annotated[list[str], Field(..., examples=[["tagname"]])] = []


class AlertGroupUpdate(AlertGroupBase):
    owner: Annotated[str, Field(...)] = None


class AlertGroup(PopularityVoted, FavoriteLink, AlertGroupBase, ResultBase):
    alert_count: Annotated[int, Field(...)] = 0
    open_count: Annotated[int, Field(...)] = 0
    closed_count: Annotated[int, Field(...)] = 0
    promoted_count: Annotated[int, Field(...)] = 0
    tags: Annotated[list[Tag], Field(...)] = []
    sources: Annotated[list[Source], Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class AlertGroupDetailed(AlertGroup):
    full_column_names: Annotated[list[str], Field(...)]
    full_column_types: Annotated[list[str | None], Field(...)]
    full_alert_data_flaired: Annotated[list[dict], Field(...)]
    full_alert_data: Annotated[list[dict], Field(...)]
    associated_sig_guide_map: Annotated[dict, Field(...)] = {}
    tags: Annotated[list[Tag], Field(...)] = []
    sources: Annotated[list[Source], Field(...)] = []

    # Pydantic doesn't like list association proxies
    @field_validator(
        "full_column_names",
        "full_column_types",
        "full_alert_data_flaired",
        "full_alert_data",
        mode="before",
    )
    def coerce_to_list(cls, v):
        return list(v)


class AlertGroupSearch(SearchBase):
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    subject: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tlp: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    message_id: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    source: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tag: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    status: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    alert_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    promoted_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    open_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    closed_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    first_view: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    parsed: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    view_count: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        value = value.strip()
        if attr == "owner" or attr == "subject" or attr == "message_id" or attr == "source" or attr == "tag":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "alert_count" or attr == "promoted_count" or attr == "open_count" or attr == "closed_count" or attr == "view_count":
            return int(value)
        elif attr == "first_view":
            return parser.parse(value)
        elif attr == "parsed":
            return is_bool(value)
        elif attr == "status":
            return StatusEnum(value)
        else:
            return super().type_mapping(attr, value)
