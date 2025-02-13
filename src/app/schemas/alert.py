from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, field_validator, ConfigDict, Field

from app.core.config import settings
from app.enums import StatusEnum, TlpEnum
from app.schemas.alertgroupschema import AlertGroupSchemaColumn
from app.schemas.response import SearchBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink
from app.utils import sanitize_html, is_bool


class AlertDataBase(BaseModel):
    alert_id: Annotated[int, Field(...)]
    schema_key_id: Annotated[int, Field(...)]
    schema_column: Annotated[AlertGroupSchemaColumn | None, Field(...)] = None
    data_value: Annotated[str | None, Field(...)] = None
    data_value_flaired: Annotated[str | None, Field(...)] = None


class AlertDataCreate(BaseModel):
    name: Annotated[str, Field(...)]
    value: Annotated[str, Field(...)]
    value_flaired: Annotated[str | None, Field(...)] = None

    @field_validator("value", mode="before")
    def sanitize(cls, v: str):
        return sanitize_html(v)

    @field_validator("value_flaired", mode="before")
    def sanitize_flaired(cls, v: str):
        return sanitize_html(v, flaired_alert=True)


class AlertDataUpdate(BaseModel):
    name: Annotated[str, Field(...)]
    value: Annotated[str | None, Field(...)] = None
    value_flaired: Annotated[str | None, Field(...)] = None

    @field_validator("value", mode="before")
    def sanitize(cls, v: str):
        return sanitize_html(v)

    @field_validator("value_flaired", mode="before")
    def sanitize_flaired(cls, v: str):
        return sanitize_html(v, flaired_alert=True)


# pretty
class AlertData(AlertDataBase, FavoriteLink):
    model_config = ConfigDict(from_attributes=True)


class AlertBase(BaseModel):
    owner: Annotated[str, Field(...)]
    tlp: Annotated[TlpEnum | None, Field(..., examples=[a.value for a in list(TlpEnum)])] = TlpEnum.unset
    status: Annotated[StatusEnum | None, Field(..., examples=[a.value for a in list(StatusEnum)])] = StatusEnum.open
    parsed: Annotated[bool | None, Field(...)] = False
    alertgroup_id: Annotated[int | None, Field(...)] = None


class AlertCreate(AlertBase):
    owner: Annotated[str | None, Field(...)] = settings.FIRST_SUPERUSER_USERNAME
    data: Annotated[list[AlertDataCreate] | None, Field(...)] = None

    @field_validator("data", mode="before")
    def convert_dict_to_alert_data(cls, v):
        if isinstance(v, dict):
            return [
                AlertDataCreate(name=key, value=val)
                for key, val in v.items()
            ]
        else:
            return v

    model_config = ConfigDict(use_enum_values=True)


class AlertAdd(AlertBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME
    data: Annotated[dict | None, Field(...)] = None
    data_flaired: Annotated[dict | None, Field(...)] = None

    @field_validator("data", mode="before")
    def sanitize(cls, v):
        if v and isinstance(v, dict):
            return {k: sanitize_html(v[k]) for k in v}
        else:
            return v

    @field_validator("data_flaired", mode="before")
    def sanitize_flaired(cls, v):
        if v and isinstance(v, dict):
            return {k: sanitize_html(v[k], flaired_alert=True) for k in v}
        else:
            return v

    model_config = ConfigDict(use_enum_values=True)


class AlertUpdate(AlertAdd):
    owner: Annotated[str | None, Field(...)] = None


# pretty
class Alert(AlertBase, PopularityVoted, FavoriteLink):
    id: Annotated[int, Field(...)]
    entry_count: Annotated[int | None, Field(...)] = 0
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    alertgroup_id: Annotated[int, Field(...)]
    alertgroup_subject: Annotated[str | None, Field(...)] = None
    data: Annotated[dict | None, Field(...)] = {}
    data_flaired: Annotated[dict | None, Field(...)] = {}
                                                                                                                      
    model_config = ConfigDict(from_attributes=True)


class AlertSearch(SearchBase):
    owner: Annotated[str | None, Field(...)] = None
    tlp: Annotated[str | None, Field(...)] = None
    parsed: Annotated[str | None, Field(...)] = None
    alertgroup_id: Annotated[str | None, Field(...)] = None
    entry_count: Annotated[str | None, Field(...)] = None
    promoted_to: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        value = value.strip()
        if attr == "owner" or attr == "promoted_to":
            return value
        elif attr == "tlp":
            return TlpEnum(value)
        elif attr == "parsed":
            return is_bool(value)
        elif attr == "alertgroup_id" or attr == "entry_count":
            return int(value)
        else:
            return super().type_mapping(attr, value)
