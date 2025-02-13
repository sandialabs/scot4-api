from datetime import datetime
from dateutil import parser
from typing import Any, Annotated

from pydantic import BaseModel, field_validator, ConfigDict, Field

from app.enums import TlpEnum, StatusEnum
from app.core.config import settings
from app.schemas.alert import AlertCreate
from app.schemas.alertgroupschema import AlertGroupSchemaColumnCreate
from app.schemas.response import SearchBase
from app.schemas.tag import Tag
from app.schemas.source import Source
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink
from app.utils import is_bool


class AlertGroupBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    view_count: Annotated[int | None, Field(...)] = 0
    first_view: Annotated[datetime | None, Field(...)] = None
    message_id: Annotated[str | None, Field(...)] = None
    back_refs: Annotated[str | None, Field(...)] = None
    subject: Annotated[str | None, Field(...)] = ""
    sources: Annotated[list[Source] | None, Field(...)] = []
    tags: Annotated[list[Tag] | None, Field(...)] = []

    model_config = ConfigDict(
        use_enum_values=True,
    )


class AlertGroupDetailedCreate(AlertGroupBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME
    alert_schema: Annotated[list[AlertGroupSchemaColumnCreate] | None, Field(...)] = []
    alerts: Annotated[list[AlertCreate] | None, Field(...)] = []
    sources: Annotated[list[str] | None, Field(...)] = []
    tags: Annotated[list[str] | None, Field(...)] = []

    model_config = ConfigDict(
        use_enum_values=True,
    )


class AlertGroupCreate(AlertGroupBase):
    sources: Annotated[list[str] | None, Field(...)] = []
    tags: Annotated[list[str] | None, Field(...)] = []


class AlertGroupUpdate(AlertGroupBase):
    owner: Annotated[str | None, Field(...)] = None


class AlertGroup(AlertGroupBase, PopularityVoted, FavoriteLink):
    id: Annotated[int, Field(...)]
    alert_count: Annotated[int | None, Field(...)] = 0
    open_count: Annotated[int | None, Field(...)] = 0
    closed_count: Annotated[int | None, Field(...)] = 0
    promoted_count: Annotated[int | None, Field(...)] = 0
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()

    model_config = ConfigDict(from_attributes=True)


class AlertGroupDetailed(AlertGroup):
    full_column_names: Annotated[list[str], Field(...)]
    full_column_types: Annotated[list[str | None], Field(...)]
    full_alert_data_flaired: Annotated[list[dict], Field(...)]
    full_alert_data: Annotated[list[dict], Field(...)]
    associated_sig_guide_map: Annotated[dict | None, Field(...)] = {}
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

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
    owner: Annotated[str | None, Field(...)] = None
    subject: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    message_id: Annotated[str | None, Field(...)] = None
    source: Annotated[str | None, Field(...)] = None
    tag: Annotated[str | None, Field(...)] = None
    status: Annotated[str | None, Field(...)] = None
    alert_count: Annotated[str | None, Field(...)] = None
    promoted_count: Annotated[str | None, Field(...)] = None
    open_count: Annotated[str | None, Field(...)] = None
    closed_count: Annotated[str | None, Field(...)] = None
    first_view: Annotated[str | None, Field(...)] = None
    parsed: Annotated[str | None, Field(...)] = None
    view_count: Annotated[str | None, Field(...)] = None

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
