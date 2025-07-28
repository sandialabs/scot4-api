import json
from datetime import datetime
from typing import Any, Annotated, Tuple
from dateutil import parser

from pydantic import BaseModel, Json, field_validator, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema


class AuditBase(BaseModel):
    when_date: Annotated[datetime, Field(...)]
    username: Annotated[str | None, Field(...)] = None
    what: Annotated[str, Field(...)]
    thing_type: Annotated[str | None, Field(...)] = None
    thing_subtype: Annotated[str | None, Field(...)] = None
    thing_id: Annotated[int | None, Field(...)] = None
    src_ip: Annotated[str | None, Field(...)] = None
    user_agent: Annotated[str | None, Field(...)] = None
    audit_data_ver: Annotated[str | None, Field(...)] = None
    audit_data: Annotated[Json | None, Field(..., examples=[{}])] = None

    @field_validator("audit_data", mode="before")
    def convert_data_to_json(cls, v):
        if isinstance(v, (list, dict)):
            return json.dumps(v).encode("utf-8")
        return v


class AuditCreate(AuditBase):
    pass


class AuditUpdate(AuditBase):
    when_date: Annotated[datetime | SkipJsonSchema[None], Field(...)] = None
    what: Annotated[str | SkipJsonSchema[None], Field(...)] = None


# pretty
class Audit(AuditBase):
    id: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class AuditSearch(BaseModel):
    id: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    when_date: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    username: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    what: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    thing_type: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    thing_id: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "id" or attr == "thing_id":
            return int(value)
        elif attr == "when_date":
            if isinstance(value, tuple) and len(value) == 2:
                return (parser.parse(value[0]), parser.parse(value[1]))
            else:
                return parser.parse(value)
        elif attr == "username" or attr == "what" or attr == "thing_type":
            return value
        else:
            raise AttributeError(f"Unknown attribute {attr}")
