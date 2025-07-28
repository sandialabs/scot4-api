from typing import Any, Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session
from pydantic import create_model, Field
from pydantic.json_schema import SkipJsonSchema

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum, EntryClassEnum, SpecialMetricEnum
from app.utils import send_flair_entry_request, create_schema_details
from app.schemas.permission import PermissionList

from .generic import (
    generic_delete,
    generic_entities,
    generic_put,
    generic_source_add_remove,
    generic_tag_untag,
    generic_undelete,
    generic_reflair,
    generic_search,
    generic_export,
    generic_upvote_and_downvote,
    generic_user_links
)

router = APIRouter()


@router.get(
    "/{id}",
    response_model=schemas.EntryWithParent,
    summary="Get an entry",
    description="Get a single entry by id",
    dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.entry, PermissionEnum.read))],
)
def read_object(
    *,
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
) -> Any:
    entry = crud.entry.get(db, id, audit_logger)
    if not entry:
        raise HTTPException(404, f"{TargetTypeEnum.entry.value} not found")
    # To read an entry, you also need permission on its parent object
    # Will raise HTTPException on failure
    deps.PermissionCheckId(entry.target_type, PermissionEnum.read)(entry.target_id, db, user, roles)
    return entry


# Create post, put, delete, tag, and source endpoints
generic_put(router, crud.entry, TargetTypeEnum.entry, schemas.Entry, schemas.EntryUpdate)
generic_delete(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_search(router, crud.entry, TargetTypeEnum.entry, schemas.EntrySearch, schemas.EntryWithParent)
generic_undelete(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_tag_untag(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_source_add_remove(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_entities(router, TargetTypeEnum.entry)
generic_reflair(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_export(router, crud.entry, TargetTypeEnum.entry)
generic_upvote_and_downvote(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)
generic_user_links(router, crud.entry, TargetTypeEnum.entry, schemas.Entry)


def GenLegacyFormat(name, model):
    if not name:
        return object
    return create_model('LegacyFormat', **{name: (SkipJsonSchema[model | None], Field(None, exclude=True))})


# create a dummy schema that can handle permissions and the legacy creation format
class PostObject(PermissionList, schemas.EntryCreate, GenLegacyFormat(TargetTypeEnum.entry.value, schemas.EntryCreate)):
    pass


description, examples = create_schema_details(PostObject, "Create an entry, optionally granting read, write, or delete permissions. It will otherwise inherit the permissions of its parent entry or object.\n")
many_description, many_examples = create_schema_details(PostObject, "Create multiple entries, optionally granting read, write, or delete permissions. They will otherwise inherit the permissions of their parent entry or object.\n")
for example in many_examples:
    many_examples[example]["value"] = [many_examples[example]["value"]]


@router.post(
    "/many",
    response_model=list[schemas.Entry],
    summary="Create many entries",
    description=many_description
)
def create_entries(
    *,
    entries: Annotated[list[PostObject], Body(openapi_examples=many_examples)],
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    current_user: schemas.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Any:
    _obj = []
    for entry in entries:
        _obj.append(create_entry(entry=entry, db=db, audit_logger=audit_logger, current_roles=current_roles, current_user=current_user, background_tasks=background_tasks))
    return _obj


@router.post(
    "/",
    response_model=schemas.Entry,
    summary="Create an entry",
    description=description
)
def create_entry(
    *,
    entry: Annotated[PostObject, Body(openapi_examples=examples)],
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    current_user: schemas.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Any:
    # The user must have modify permissions on the parent object
    # Will raise HTTPException on failure
    deps.PermissionCheckId(entry.target_type, PermissionEnum.modify)(entry.target_id, db, current_user, current_roles)
    permissions = getattr(entry, "permissions", None)
    del entry.permissions

    # if there is a legacy object key, use that instead of the actual object
    if getattr(entry, TargetTypeEnum.entry.value, None) is not None:
        entry = getattr(entry, TargetTypeEnum.entry.value)
    elif hasattr(entry, TargetTypeEnum.entry.value):
        delattr(entry, TargetTypeEnum.entry.value)

    if permissions is not None:
        _obj = crud.entry.create_with_permissions(db, obj_in=entry, perm_in=permissions, audit_logger=audit_logger)
    elif entry.parent_entry_id is not None:
        _obj = crud.entry.create_in_object(db, obj_in=entry, source_type=TargetTypeEnum.entry, source_id=entry.parent_entry_id, audit_logger=audit_logger)
    else:
        _obj = crud.entry.create_in_object(db, obj_in=entry, source_type=entry.target_type, source_id=entry.target_id, audit_logger=audit_logger)

    if entry.target_type is TargetTypeEnum.event and entry.entry_class is not EntryClassEnum.promotion:
        # If this entry targets an event and it isn't a promotion, could trigger a mttc metric
        _target_obj = crud.event.get(db_session=db, _id=entry.target_id, audit_logger=audit_logger)

        crud.special_metric.get_or_create(
            db_session=db,
            obj_in=schemas.SpecialMetricCreate(
                target_id=entry.target_id,
                target_type=entry.target_type,
                metric_type=SpecialMetricEnum.mttc,
                start_time=_target_obj.created,
                end_time=datetime.now(timezone.utc)
            ),
            audit_logger=audit_logger
        )

    background_tasks.add_task(send_flair_entry_request, TargetTypeEnum.entry, _obj)
    crud.notification.send_create_notifications(db, _obj, current_user)
    return _obj
