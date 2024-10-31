from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict

from app.enums import PermissionEnum, TargetTypeEnum


class PermissionList(BaseModel):
    permissions: Annotated[
        dict[PermissionEnum, list[str | int]] | None,
        Field(
            ...,
            description="Provide a dictionary with the permission type as the key and a list of role ids or role names",
            examples=[{a.value: [0, "admin"]} for a in list(PermissionEnum)]
        )
    ] = None


class PermissionBase(BaseModel):
    role_id: Annotated[int, Field(...)]
    target_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    target_id: Annotated[int, Field(...)]
    permission: Annotated[PermissionEnum, Field(..., examples=[a.value for a in list(PermissionEnum)])]


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(PermissionBase):
    role_id: Annotated[int | None, Field(...)] = None
    target_type: Annotated[TargetTypeEnum | None, Field(..., examples=[a.value for a in list(TargetTypeEnum)])] = TargetTypeEnum.none
    target_id: Annotated[int | None, Field(...)] = None
    permission: Annotated[PermissionEnum | None, Field(..., examples=[a.value for a in list(PermissionEnum)])] = None


# For mass setting of permissions on one object
class PermissionSetMass(PermissionList):
    target_type: Annotated[TargetTypeEnum, Field(..., examples=[a.value for a in list(TargetTypeEnum)])]
    target_id: Annotated[int, Field(...)]


class Permission(PermissionBase):
    id: Annotated[int, Field(...)]

    model_config = ConfigDict(from_attributes=True)
