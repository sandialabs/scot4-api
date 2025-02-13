from typing import Union, Annotated
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum

router = APIRouter()


# Response model is union of every possible target type
# I'm not sure there's a better way to do this
# Right now this misbehaves when promoting to something weird (like an entity)
# Ordering in the response model list usually causes the correct behavior
@router.post(
    "/",
    response_model=Union[
        schemas.Event,
        schemas.Incident,
        schemas.Intel,
        schemas.Product,
        schemas.VulnTrack
    ],
)
def promote(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    source: Annotated[list[dict], Body(...)],
    destination: Annotated[TargetTypeEnum, Body(...)],
    destination_id: Annotated[int | None, Body(...)] = None,
    tags: Annotated[list[str] | None, Body(...)] = None,
    sources: Annotated[list[str] | None, Body()] = None,
    permissions: Annotated[dict[TargetTypeEnum, list[str | int]] | None, Body(...)] = None
):
    """
    Promote one or more source objects into a destination object
    """
    # Check permissions on source objects
    try:
        for s in source:
            target_type = s["type"]
            target_id = s["id"]
            if not deps.PermissionCheckId(target_type, PermissionEnum.read)(target_id, db, current_user, current_roles):
                raise ValueError(f"{target_type} with id {target_id} does not exist or you do not have permission to access it")
    except (IndexError, ValueError) as e:
        raise HTTPException(422, f"Error processing promotion: {e}")
    # User needs modify permissions on the destination if it already exists
    if destination_id is not None:
        if not deps.PermissionCheckId(destination, PermissionEnum.modify)(destination_id, db, current_user, current_roles):
            raise HTTPException(422, f"{destination.value} with id {destination_id} does not exist or you do not have permission to modify it")
    # Do the promotion
    try:
        return crud.promotion.promote(db, source, destination, destination_id, tags, current_user, sources, permissions, audit_logger)
    except ValueError as e:
        raise HTTPException(422, f"Error processing promotion: {e}")
