from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum

from .generic import (
    generic_delete,
    generic_get,
    generic_post,
    generic_put,
    generic_undelete,
    generic_search
)

router = APIRouter()
tag_read_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.tag, PermissionEnum.read))


# Create get, post, put, and delete endpoints
generic_get(router, crud.tag, TargetTypeEnum.tag, schemas.Tag)
generic_post(router, crud.tag, TargetTypeEnum.tag, schemas.Tag, schemas.TagCreate)
generic_put(router, crud.tag, TargetTypeEnum.tag, schemas.Tag, schemas.TagUpdate)
generic_delete(router, crud.tag, TargetTypeEnum.tag, schemas.Tag)
generic_undelete(router, crud.tag, TargetTypeEnum.tag, schemas.Tag)
generic_search(router, crud.tag, TargetTypeEnum.tag, schemas.TagSearch, schemas.Tag)


@router.post("/{id}/tag", response_model=schemas.Tag, dependencies=[tag_read_dep])
def apply_tag(
    id: Annotated[int, Path(...)],
    target_type: Annotated[TargetTypeEnum, Body(...)],
    target_id: Annotated[int, Body(...)],
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Assign a tag to an object; you can only tag an object if you have read
    permissions on the tag and modify permissions on the object.
    """
    # Get effective permissions on target object
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(
            target_id, db, user, roles
    ):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, create a link to the tag
    tag = crud.tag.assign(
        db,
        tag_id=id,
        target_type=target_type,
        target_id=target_id,
        audit_logger=audit_logger,
    )
    if not tag:
        raise HTTPException(404, f"Tag {id} not found")

    return tag


@router.post("/tag_by_name", response_model=schemas.Tag)
def add_tag(
    target_type: Annotated[TargetTypeEnum, Body(...)],
    target_id: Annotated[int, Body(...)],
    tag_name: Annotated[str, Body(...)],
    tag_description: Annotated[str, Body(...)],
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Assign a tag to an object; you can only tag an object if you have read
    permissions on the tag and modify permissions on the object.
    """
    # Get effective permissions on target object
    current_tag = crud.tag.get_by_name(db, tag_name)  # Does the tag exist?
    if current_tag:
        if not deps.PermissionCheckId(TargetTypeEnum.tag, PermissionEnum.read)(
            id=current_tag.id, db=db, user=user, roles=roles
        ):
            raise HTTPException(403, "You do not have permission to access this resource, or it does not exist")
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(
            target_id, db, user, roles
    ):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, create a link to the tag
    return crud.tag.assign_by_name(
        db,
        tag_name=tag_name,
        target_type=target_type,
        target_id=target_id,
        tag_description=tag_description,
        create=True,
        audit_logger=audit_logger,
    )


@router.post("/{id}/untag", response_model=schemas.Tag, dependencies=[tag_read_dep])
def remove_tag(
    id: Annotated[int, Path(...)],
    target_type: Annotated[TargetTypeEnum, Body(...)],
    target_id: Annotated[int, Body(...)],
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Assign a tag to an object; you can only remove a tag from an object if
    you have read permissions on the tag and modify permissions on the object.
    """
    # Get effective permissions on target object
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(
            target_id, db, user, roles
    ):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, delete all links to the tag
    tag = crud.tag.unassign(
        db,
        tag_id=id,
        target_type=target_type,
        target_id=target_id,
        audit_logger=audit_logger,
    )
    if tag:
        return tag
    else:
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} is not tagged with tag {id}")


@router.get(
    "/{id}/appearance",
    response_model=schemas.ListResponse[schemas.Appearance],
    dependencies=[tag_read_dep],
)
def tag_appearances(
    id: Annotated[int, Path(...)],
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = 100,
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    filter_dict = {"value_type": TargetTypeEnum.tag.value, "value_id": id}
    _appear, count = crud.appearance.query_with_filters(
        db_session=db, roles=roles, filter_dict=filter_dict, skip=skip, limit=limit
    )
    return {"totalCount": count, "resultCount": len(_appear), "result": _appear}
