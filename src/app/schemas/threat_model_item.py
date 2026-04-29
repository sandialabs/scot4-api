import re
from typing import Any, Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo
from pydantic.json_schema import SkipJsonSchema
from packaging.version import Version

from app.core.config import settings
from app.enums import ThreatModelName
from app.schemas.source import Source
from app.schemas.tag import Tag
from app.schemas.response import SearchBase, ResultBase
from app.schemas.popularity import PopularityVoted
from app.schemas.user_links import FavoriteLink


data_examples = [{
    "url": "string",
    "tactic": "string",
    "version": "1.0"
}]

data_description = """
Depending on the `threat_model_name` the required fields are different and must be included, and other fields can be added as needed. The following keys are required:
    - MITRE ATTACK: `url`, `title`, `description`, `version`, `tactic`
"""

 
class ThreatModelItemBase(BaseModel):
    threat_model_name: Annotated[ThreatModelName, Field(..., examples=[a.value for a in list(ThreatModelName)])] = ThreatModelName.attack
    threat_model_id: Annotated[str | None, Field(...)] = None
    title: Annotated[str | None, Field(...)] = None
    description: Annotated[str | None, Field(...)] = None
    owner: Annotated[str, Field(...)]
    data: Annotated[dict[str, Any] | None, Field(..., examples=data_examples, description=data_description)] = None

    @field_validator("threat_model_id")
    def check_valid_id(cls, v: str | None, info: ValidationInfo):
        if v is not None:
            v = v.strip()
            if info.data.get("threat_model_name") and info.data.get("threat_model_name") == ThreatModelName.attack:
                # threat_model_id must be of format T[0000] OR T[0000].[000]
                if not re.match(r"^T\d{4}\.\d{3}$|^T\d{4}$", v):
                    raise ValueError("threat_model_id is not valid must be of format T1234 or T1234.123")

        return v
    
    @field_validator("data")
    def check_valid_data_fields(cls, v: dict[str, Any] | None, info: ValidationInfo):
        if v is not None:
            if info.data.get("threat_model_name") and info.data.get("threat_model_name") == ThreatModelName.attack:
                # attack must have at a minimum the following key value pairs set
                if "url" not in v.keys():
                    raise ValueError("url was not provided in data")
                elif not isinstance(v["url"], str):
                    raise ValueError("url needs to be a string")
                elif v["url"] == "":
                    raise ValueError("url must be set")
                # test for proper http....?

                if "version" not in v.keys():
                    raise ValueError("version was not provided in data")
                elif v["version"] == "":
                    raise ValueError("version must be set")

                try:
                    Version(v["version"])
                except Exception as e:
                    raise ValueError("version is not valid format")
                
                if "tactics" not in v.keys():
                    raise ValueError("tactics was not provided in data")
                elif not isinstance(v["tactics"], list):
                    raise ValueError("tactics needs to be a list of strings")
                elif len(v["tactics"]) == 0:
                    raise ValueError(f"tactics must be set")
                elif not isinstance(v["tactics"][0], str):
                    raise ValueError("tactics needs to be a list of strings")
                
                # ensure that the tactics is all lower case and any extra whitespace has been removed
                v["tactics"] = [a.lower().strip() for a in v["tactics"]]

        return v

    model_config = ConfigDict(from_attributes=True)


class ThreatModelItemCreate(ThreatModelItemBase):
    owner: Annotated[str, Field(...)] = settings.FIRST_SUPERUSER_USERNAME


class ThreatModelItemUpdate(ThreatModelItemBase):
    threat_model_name: Annotated[ThreatModelName | None, Field(..., examples=[a.value for a in list(ThreatModelName)])] = None
    owner: Annotated[str | None, Field(...)] = None


class ThreatModelItem(ThreatModelItemBase, ResultBase, FavoriteLink, PopularityVoted):
    entry_count: Annotated[int, Field(...)] 
    tags: Annotated[list[Tag] | None, Field(...)] = []
    sources: Annotated[list[Source] | None, Field(...)] = []

    model_config = ConfigDict(from_attributes=True)


class ThreatModelItemSearch(SearchBase):
    threat_model_name: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    threat_model_id: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    title: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    description: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    owner: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    data: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    tag: Annotated[str | SkipJsonSchema[None], Field(...)] = None
    source: Annotated[str | SkipJsonSchema[None], Field(...)] = None

    def type_mapping(self, attr: str, value: str) -> Any:
        if attr == "threat_model_id" or attr == "tag" or attr == "source" or attr == "title" or attr == "description":
            return value
        elif attr == "threat_model_name":
            return ThreatModelName(value)
        else:
            return super().type_mapping(attr, value)
