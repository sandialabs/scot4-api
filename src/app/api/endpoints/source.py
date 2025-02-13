from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
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

# Create get, post, put, and delete endpoints
generic_get(router, crud.source, TargetTypeEnum.source, schemas.Source)
generic_post(router, crud.source, TargetTypeEnum.source, schemas.Source, schemas.SourceCreate)
generic_put(router, crud.source, TargetTypeEnum.source, schemas.Source, schemas.SourceUpdate)
generic_delete(router, crud.source, TargetTypeEnum.source, schemas.Source)
generic_undelete(router, crud.source, TargetTypeEnum.source, schemas.Source)
generic_search(router, crud.source, TargetTypeEnum.source, schemas.SourceSearch, schemas.Source)


source_read_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.source, PermissionEnum.read))


@router.post("/source_by_name", response_model=schemas.Source)
def add_source(
    target_type: Annotated[TargetTypeEnum, Body(...)],
    source_name: Annotated[str, Body(...)],
    source_description: Annotated[str, Body(...)],
    target_id: Annotated[int, Body(...)],
    user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Assign a source to an object; you can only assign a source if you have read
    permissions on the source and modify permissions on the object.
    """
    # Get effective permissions on target object
    current_source = crud.source.get_by_name(db, source_name)  # Does the tag exist?
    if current_source:
        if not deps.PermissionCheckId(TargetTypeEnum.tag, PermissionEnum.read)(current_source.id, db, user, roles):
            raise HTTPException(403, "You do not have permission to access this resource, or it does not exist")
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, user, roles):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, create a link to the source
    return crud.source.assign_by_name(db, source_name, target_type, target_id, True, source_description, audit_logger)


@router.post("/{id}/assign", response_model=schemas.Source, dependencies=[source_read_dep])
def apply_source(
    id: Annotated[int, Path(...)],
    target_type: Annotated[TargetTypeEnum, Body(...)],
    target_id: Annotated[int, Body(...)],
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Assign a source to an object; you can only assign a source if you have read
    permissions on the source and modify permissions on the object.
    """
    # Get effective permissions on target object
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, user, roles):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, create a link to the source
    _source = crud.source.assign(db, id, target_type, target_id, audit_logger)
    if not _source:
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not have source {id}")
    return _source


@router.post("/{id}/remove", response_model=schemas.Source, dependencies=[source_read_dep])
def remove_source(
    id: Annotated[int, Path(...)],
    target_type: Annotated[TargetTypeEnum, Body(...)],
    target_id: Annotated[int, Body(...)],
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Remove a source from an object; you can only remove a source from an object if
    you have read permissions on the source and modify permissions on the object.
    """
    # Get effective permissions on target object
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, user, roles):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, delete all links to the source
    source = crud.source.unassign(db, id, target_type, target_id, audit_logger)
    if source:
        return source
    else:
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not have source {id}")


@router.get(
    "/{id}/appearance",
    response_model=schemas.ListResponse[schemas.Appearance],
    dependencies=[source_read_dep],
)
def source_appearances(
    id: Annotated[int, Path(...)],
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = 100,
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    _: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    _appear, count = crud.appearance.query_with_filters(db, roles, {"value_type": TargetTypeEnum.source.value, "value_id": id}, None, skip, limit)
    return {"totalCount": count, "resultCount": len(_appear), "result": _appear}
