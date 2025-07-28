from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, Body, Query
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger, get_audit_logger, get_current_active_user, get_db, PermissionCheckId
from app.core.config import settings
from app.enums import PermissionEnum, TargetTypeEnum
from app.schemas import Permission, PermissionCreate, PermissionSetMass, User, Role
from app.utils import create_schema_details

router = APIRouter()


description, examples = create_schema_details(PermissionCreate)


@router.post("/grant", response_model=Permission, summary="Grant a permission", description=description)
async def grant_permission(
    permission_grant: Annotated[PermissionCreate, Body(..., openapi_examples=examples)],
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """
    Grant permission on a resource
    """
    # Get user's effective permissions on this object
    permissions = crud.permission.get_permissions(db, user.username, permission_grant.target_type, permission_grant.target_id)
    if (
        permission_grant.target_type == TargetTypeEnum.admin
        or permission_grant.permission == PermissionEnum.admin
    ) and not crud.user.is_superuser(user):
        raise HTTPException(403, "Only the superuser can assign admin permissions")
    # A user can grant a permission if they have admin OR modify permissions
    if (
        PermissionEnum.modify not in permissions
        and PermissionEnum.admin not in permissions
        and not crud.user.is_superuser(user)
    ):
        raise HTTPException(404, f"{permission_grant.target_type.value} with id {permission_grant.target_id} does not exist, or you do not have permission to assign access to it")
    try:
        # The user can grant this permission, so add it to the table
        return crud.permission.grant_permission(db, permission_grant, audit_logger)
    except Exception as e:
        raise HTTPException(422, str(e))


@router.post("/revoke", status_code=204, summary="Revoke a permission", description=description)
async def revoke_permission(
    permission_revoke: Annotated[PermissionCreate, Body(..., openapi_examples=examples)],
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """
    Revoke a particular permission
    """
    # Get user's effective permissions on this object
    permissions = crud.permission.get_permissions(db, user.username, permission_revoke.target_type, permission_revoke.target_id)
    # Only the superuser can revoke admin permissions
    if (
        permission_revoke.target_type == TargetTypeEnum.admin
        or permission_revoke.permission == PermissionEnum.admin
    ) and not crud.user.is_superuser(user):
        raise HTTPException(403, "Only the superuser can revoke admin permissions")
    # A user can revoke a permission if they have admin OR modify permissions
    # Note that this means users can revoke their own permissions if they
    # really want to
    if (
        PermissionEnum.modify not in permissions
        and PermissionEnum.admin not in permissions
        and not crud.user.is_superuser(user)
    ):
        raise HTTPException(404, f"{permission_revoke.target_type.value} with id {permission_revoke.target_id} does not exist, or you do not have permission to revoke access to it")

    # The user has permission to revoke this permission, now find and revoke it
    result = crud.permission.revoke_permission(db, permission_revoke, audit_logger)
    if result:
        return Response(status_code=204)
    else:
        raise HTTPException(404, "Permission not found")


description, examples = create_schema_details(PermissionSetMass,
    "Set all permissions of an item, overriding the previous permissions")


@router.post("/set", summary="Set object permissions", description=description)
async def set_permission(
    mass_permission: Annotated[PermissionSetMass, Body(..., openapi_examples=examples)],
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger),
):
    """
    Directly sets all permissions on an object
    WARNING: All permissions not in the permissions set will be revoked
    """
    # Get user's effective permissions on this object
    permissions = crud.permission.get_permissions(db, user.username, mass_permission.target_type, mass_permission.target_id)
    # You can't use this endpoint to set admin permissions
    if mass_permission.target_type == TargetTypeEnum.admin or any(
        [p == PermissionEnum.admin for p in mass_permission.permissions]
    ):
        raise HTTPException(403, "Admin permissions cannot be set through this endpoint")
    # A user can revoke a permission if they have admin OR modify permissions
    # Note that this means users can revoke all of their modify permissions
    # on a object if they want to
    if (
        PermissionEnum.modify not in permissions
        and PermissionEnum.admin not in permissions
        and not crud.user.is_superuser(user)
    ):
        raise HTTPException(404, f"You do not have permission to set access to {mass_permission.target_type.value} {mass_permission.target_id}")
    # The user has permissions to set permissions, now do it
    oldPermissions = crud.permission.get_permission_roles(db, mass_permission.target_type, mass_permission.target_id)
    try:
        for p in [PermissionEnum.read, PermissionEnum.modify, PermissionEnum.delete]:
            newPermIds = set(mass_permission.permissions.get(p, []))
            oldPermIds = set([r.id for r in oldPermissions.get(p, [])])
            revoke = oldPermIds - newPermIds
            grant = newPermIds - oldPermIds
            for roleId in revoke:
                crud.permission.revoke_permission(
                    db,
                    PermissionCreate(
                        role_id=roleId,
                        target_type=mass_permission.target_type,
                        target_id=mass_permission.target_id,
                        permission=p,
                    ),
                    audit_logger
                )
            for roleId in grant:
                crud.permission.grant_permission(
                    db,
                    PermissionCreate(
                        role_id=roleId,
                        target_type=mass_permission.target_type,
                        target_id=mass_permission.target_id,
                        permission=p,
                    ),
                    audit_logger
                )
    except Exception:
        raise HTTPException(500, "An error occurred while assigning permissions, make sure all roles being assigned exist")
    return crud.permission.get_permission_roles(db, mass_permission.target_type, mass_permission.target_id)


@router.get("/getroles", response_model=dict[PermissionEnum, list[Role]], summary="Get object permissions")
async def get_permission_roles(
    target_type: Annotated[TargetTypeEnum, Query(...)],
    target_id: Annotated[int, Query(...)],
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get which roles have what permissions on an object
    """
    # Grab all roles with access to this object
    permission_roles = crud.permission.get_permission_roles(db, target_type, target_id)
    # Get all roles which would have permission to read roles on this object
    read_perms = [PermissionEnum.read]
    read_role_ids = set([
        role.id
        for r in read_perms
        if r in permission_roles
        for role in permission_roles[r]
    ])
    if (
        not any(user_role.id in read_role_ids for user_role in user.roles)
        and not (settings.EVERYONE_ROLE_ID in read_role_ids)
        and target_type not in PermissionCheckId.type_allow_whitelist
        and not crud.user.is_superuser(user)
        and not crud.permission.user_is_admin(db, user)
    ):
        raise HTTPException(403, "You do not have permission to view roles on this object")
    return permission_roles
