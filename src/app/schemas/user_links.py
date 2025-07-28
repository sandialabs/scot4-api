from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.enums import TargetTypeEnum, UserLinkEnum
from app.schemas.response import ResultBase


class UserLinksBase(BaseModel):
    link_type: Annotated[UserLinkEnum, Field(..., examples=[a.value for a in list(UserLinkEnum)])]
    target_id: Annotated[int, Field(...)]
    target_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    owner_id: Annotated[int, Field(...)]


class UserLinksCreate(UserLinksBase):
    pass


class UserLinksUpdate(BaseModel):
    link_type: Annotated[UserLinkEnum, Field(..., examples=[a.value for a in list(UserLinkEnum)])]


# pretty
class UserLinks(UserLinksBase, ResultBase):
    name: Annotated[str | None, Field(...)] = None
    parent_target_id: Annotated[int | None, Field(...)] = None
    parent_target_type: Annotated[TargetTypeEnum | None, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = None

    model_config = ConfigDict(from_attributes=True)


def move_properties_to_end(schema: dict[str, any]):
    props = schema.get("properties", {})
    for field in FavoriteLink.model_fields:
        val = props.pop(field, None)
        if val:
            props[field] = val


# inherit to return user links
class FavoriteLink(BaseModel):
    favorite: bool = False
    subscribed: bool = False

    # Function to move the properties of the Favorite/Subscription mixin to the end of the schema
    # Makes the auto-documentation look prettier
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        if hasattr(super(), "__get_pydantic_json_schema__"):
            json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        else:
            json_schema = handler(core_schema)
            json_schema = handler.resolve_ref_schema(json_schema)
        props = json_schema.get("properties", {})
        for field in FavoriteLink.model_fields:
            val = props.pop(field, None)
            if val is not None:
                props[field] = val
        return json_schema
