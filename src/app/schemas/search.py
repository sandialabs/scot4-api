from pydantic import BaseModel, Field
from typing import Annotated


class SearchRequest(BaseModel):
    text: Annotated[str, Field(...)]


class SearchResponse(BaseModel):
    search_hits: Annotated[list, Field(...)]
