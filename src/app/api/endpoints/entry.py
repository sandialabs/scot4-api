from typing import Any, Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum, TlpEnum, EntryClassEnum
from app.utils import send_flair_entry_request, create_schema_details

from .generic import (
    generic_delete,
    generic_entities,
    generic_put,
    generic_source_add_remove,
    generic_tag_untag,
    generic_undelete,
    generic_reflair,
    generic_search,
    generic_export
)

router = APIRouter()
description, examples = create_schema_details(schemas.EntryCreate)

# Create get, post, put, delete, tag, and source endpoints
generic_export(router, crud.entry, TargetTypeEnum.entry)
generic_put(
    router, crud.entry, TargetTypeEnum.entry, schemas.Entry, schemas.EntryUpdate
)
generic_delete(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_undelete(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_tag_untag(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_source_add_remove(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_entities(router, TargetTypeEnum.entry)
generic_reflair(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_search(router, crud.entry, TargetTypeEnum.entry, schemas.EntrySearch, schemas.Entry)

read_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.entry, PermissionEnum.read))
modify_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.entry, PermissionEnum.modify))


@router.get(
    "/{id}",
    response_model=schemas.EntryWithParent,
    summary="Get an entry",
    description="Get a single entry by id",
    dependencies=[read_dep],
)
def read_object(
    *,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    id: int,
) -> Any:
    entry = crud.entry.get(db_session=db, _id=id, audit_logger=audit_logger)
    if not entry:
        raise HTTPException(404, f"{TargetTypeEnum.entry.value} not found")
    parent_permission_check = deps.PermissionCheckId(
        entry.target_type, PermissionEnum.read
    )
    # To read an entry, you also need permission on its parent object
    # Will raise HTTPException on failure
    parent_permission_check(entry.target_id, db, user, roles)
    return entry


@router.post(
    "/",
    response_model=schemas.Entry,
    summary="Create an entry",
    description="Create an entry, optionally granting read, "
    "write, or delete permissions. It will otherwise inherit "
    "the permissions of its parent entry or object.\n" + description
)
def create_entry(
    *,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    entry: Annotated[schemas.EntryCreate, Body(..., openapi_examples=examples)],
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    current_user: schemas.User = Depends(deps.get_current_active_user),
    permissions: Annotated[dict[PermissionEnum, list[str | int]], Body(...)] = None,
    background_tasks: BackgroundTasks,
) -> Any:
    # The user must have modify permissions on the parent object
    parent_permission_check = deps.PermissionCheckId(
        entry.target_type, PermissionEnum.modify
    )
    # Will raise HTTPException on failure
    parent_permission_check(entry.target_id, db, current_user, current_roles)
    if permissions is not None:
        _obj = crud.entry.create_with_permissions(
            db_session=db, obj_in=entry, perm_in=permissions, audit_logger=audit_logger
        )
    elif entry.parent_entry_id is not None:
        _obj = crud.entry.create_in_object(
            db_session=db,
            obj_in=entry,
            source_type=TargetTypeEnum.entry,
            source_id=entry.parent_entry_id,
            audit_logger=audit_logger,
        )
    else:
        _obj = crud.entry.create_in_object(
            db_session=db,
            obj_in=entry,
            source_type=entry.target_type,
            source_id=entry.target_id,
            audit_logger=audit_logger,
        )
    background_tasks.add_task(send_flair_entry_request, TargetTypeEnum.entry, _obj)
    return _obj
