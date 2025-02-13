from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.enums import TargetTypeEnum, UserLinkEnum


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
class UserLinks(UserLinksBase):
    id: Annotated[int, Field(...)]
    name: Annotated[str | None, Field(...)] = None
    parent_target_id: Annotated[int | None, Field(...)] = None
    parent_target_type: Annotated[TargetTypeEnum | None, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = None
    created: Annotated[datetime | None, Field(...)] = None
    modified: Annotated[datetime | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)


# inherit to return user links
class FavoriteLink(BaseModel):
    favorite: Annotated[bool | None, Field(...)] = False
    subscribed: Annotated[bool | None, Field(...)] = False
