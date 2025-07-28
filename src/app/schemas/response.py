from datetime import datetime
from typing import Generic, TypeVar, Any, Annotated
from dateutil import parser
from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

BaseResponseType = TypeVar("BaseResponseType", bound=BaseModel)


class ListResponse(BaseModel, Generic[BaseResponseType]):
    resultCount: Annotated[int, Field(...)]
    totalCount: Annotated[int, Field(...)]
    result: Annotated[list[BaseResponseType], Field(...)]


class ResultBase(BaseModel):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()


class SearchBase(BaseModel):
    id: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    created: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    modified: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "id":
            return int(value)
        elif attr == "created" or attr == "modified":
            return parser.parse(value)
        else:
            raise AttributeError(f"Unknown attribute {attr}")
