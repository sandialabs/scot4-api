from pydantic import BaseModel, Field
from typing import Annotated
from dateutil import parser
from app.enums import TargetTypeEnum
from app.schemas.response import SearchBase


class SearchRequest(BaseModel):
    text: Annotated[str, Field(...)]
    entry_id: Annotated[str | None, Field(...)] = None
    created: Annotated[str | None, Field(...)] = None
    modified: Annotated[str | None, Field(...)] = None
    sort: Annotated[str | list[str] | None, Field(...)] = None
    owner: Annotated[str | None, Field(...)] = None
    target_type: Annotated[str | None, Field(...)] = None
    target_id: Annotated[str | None, Field(...)] = None
    popularity_count: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str):
        if attr == "owner" or attr == "text" or attr == "sort":
            return value
        elif attr == "target_type":
            return TargetTypeEnum(value).value
        elif attr == "target_id" or attr == "popularity_count" or attr == "entry_id":
            return int(value)
        elif attr == "created" or attr == "modified":
            return parser.parse(value).timestamp()
        else:
            return super().type_mapping(attr, value)


class SearchResponse(BaseModel):
    search_hits: Annotated[list, Field(...)]
