from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.schemas import EntityClass, EntityType
from app.schemas.response import SearchBase


class PivotBase(BaseModel):
    title: Annotated[str, Field(...)]
    template: Annotated[str, Field(...)]
    description: Annotated[str, Field(...)]


class PivotCreate(PivotBase):
    title: Annotated[str | None, Field(...)] = ""
    template: Annotated[str | None, Field(...)] = ""
    description: Annotated[str | None, Field(...)] = ""


class PivotUpdate(PivotBase):
    title: Annotated[str | None, Field(...)] = None
    template: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None


class PivotAddEntityClasses(BaseModel):
    entity_classes: Annotated[list[str | int], Field(...)]


class PivotAddEntityTypes(BaseModel):
    entity_types: Annotated[list[str | int], Field(...)]


class Pivot(PivotBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime | None, Field(...)] = datetime.now()
    modified: Annotated[datetime | None, Field(...)] = datetime.now()
    pivot_value: Annotated[str | None, Field(...)] = None
    entity_classes: Annotated[list[EntityClass] | None, Field(...)] = None
    entity_types: Annotated[list[EntityType] | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)


class PivotSearch(SearchBase):
    title: Annotated[str | None, Field(...)] = None
    template: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "title" or attr == "template" or attr == "description":
            return value
        else:
            return super().type_mapping(attr, value)
