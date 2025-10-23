import os

from pydantic import BaseModel, ValidationError, create_model, Field
from pydantic.json_schema import SkipJsonSchema
from typing import Any, Annotated
from fastapi import BackgroundTasks, Body, Depends, HTTPException, APIRouter, Path, Query
from sqlalchemy.orm import Session
from urllib.parse import quote
from fastapi.responses import FileResponse
from datetime import datetime, timezone

from app import crud, models, schemas
from app.crud.base import CRUDBase
from app.api import deps
from app.schemas.response import SearchBase
from app.schemas.permission import PermissionList
from app.enums import PermissionEnum, TargetTypeEnum, EntryClassEnum, ExportFormatEnum, PopularityMetricEnum, UserLinkEnum, StatusEnum, SpecialMetricEnum
from app.utils import send_flair_entry_request, send_reflair_request, create_schema_details, get_search_filters
from app.export import export_object


def gen_pretty_name(pretty_name: str | None, target_type: TargetTypeEnum):
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name.replace("_", " ")
        else:
            pretty_name = "<NO NAME>"
    return pretty_name


def pluralize_name(name: str):
    if name.endswith("y"):
        return name[:-1] + "ies"
    elif name.endswith(("h", "s", "z")):
        return name + "es"
    return name + "s"


def generic_post(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    create_schema: BaseModel,
    pretty_name: str | None = None,
    admin_only: bool = False,
    permissions: bool = True,
    many: bool = True,
):
    """
    Creates a POST endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    create_schema - The create schema for the object (e.g. EventCreate)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    admin_only (optional) - Set the API endpoint for admin users only (defaults to False)
    permissions (optional) - Give the object the ability to add default permissions (defaults to True)
    many (optional) - Create a many API endpoint as well to all for creating multiple objects at once
    """
    # "Legacy" format where there's a top-level item key
    def GenLegacyFormat(name, model):
        if not name:
            return object
        return create_model('LegacyFormat', **{name: (SkipJsonSchema[model | None], Field(None, exclude=True))})

    if permissions:
        # create a dummy schema that can handle permissions and the legacy creation format
        class PostObject(PermissionList, create_schema, GenLegacyFormat(target_type.value, create_schema)):
            pass
    else:
        # create a dummy schema that can handle permissions and the legacy creation format
        class PostObject(create_schema, GenLegacyFormat(target_type.value, create_schema)):
            pass

    pretty_name = gen_pretty_name(pretty_name, target_type)
    description = f"Create {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'}  {pretty_name}, optionally setting read, write, or delete permissions"

    if admin_only:
        dependencies = [Depends(deps.admin_only)]
        description += " (admins only)"
    else:
        dependencies = []

    description, examples = create_schema_details(PostObject, description)

    @router.post(
        "/",
        response_model=response_schema,
        summary=f"Create {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=description,
        dependencies=dependencies
    )
    def create_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        obj: Annotated[PostObject, Body(..., openapi_examples=examples, alias=pretty_name.lower())],
        current_user: models.User = Depends(deps.get_current_active_user),
        background_tasks: BackgroundTasks,
    ) -> Any:
        # get any permissions
        permissions = None
        if hasattr(obj, "permissions"):
            permissions = getattr(obj, "permissions", None)
            del obj.permissions

        # if there is a legacy object key, use that instead of the actual object
        if target_type.value:
            if getattr(obj, target_type.value, None) is not None:
                obj = getattr(obj, target_type.value)
            elif hasattr(obj, target_type.value):
                delattr(obj, target_type.value)

        if target_type == TargetTypeEnum.none:
            _obj = crud_type.create(db, obj_in=obj, audit_logger=audit_logger)

        elif permissions is not None:
            _obj = crud_type.create_with_permissions(db, obj_in=obj, perm_in=permissions, audit_logger=audit_logger)
        else:
            _obj = crud_type.create_with_owner(db, obj_in=obj, owner=current_user, audit_logger=audit_logger)

        if target_type == TargetTypeEnum.entry:
            obj_to_flair = _obj.entry_data["html"]
            background_tasks.add_task(send_reflair_request, _obj.id, TargetTypeEnum.entry, obj_to_flair)
        if target_type == TargetTypeEnum.alertgroup:
            obj_to_flair = {
                "alerts": [{"id": a.id, "row": dict(a.data)} for a in _obj.alerts]
            }
            background_tasks.add_task(send_reflair_request, _obj.id, TargetTypeEnum.alertgroup, obj_to_flair)
        if target_type == TargetTypeEnum.remote_flair:
            background_tasks.add_task(send_reflair_request, _obj.id, TargetTypeEnum.remote_flair, _obj.html)
        crud.notification.send_create_notifications(db, _obj, current_user)

        return _obj

    if many:
        examples = dict(examples)  # Make a copy of examples
        for example in examples:
            examples[example] = dict(examples[example])  # Deep copy each example
            examples[example]["value"] = [examples[example]["value"]]
        description = description.replace(
            f"Create {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'}",
            "Create one or more"
        )

        @router.post(
            "/many",
            response_model=list[response_schema],
            summary=f"Create many {pluralize_name(pretty_name)}",
            description=description,
            dependencies=dependencies
        )
        def create_objects(
            *,
            db: Session = Depends(deps.get_db),
            audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
            objs: Annotated[list[PostObject], Body(..., openapi_examples=examples, alias=pretty_name.lower())],
            current_user: models.User = Depends(deps.get_current_active_user),
            background_tasks: BackgroundTasks,
        ) -> Any:
            _objs = []
            for obj in objs:
                _objs.append(create_object(db=db, audit_logger=audit_logger, obj=obj, current_user=current_user, background_tasks=background_tasks))

            return _objs


def generic_put(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    update_schema: BaseModel,
    pretty_name: str | None = None,
    admin_only: bool = False,
    many: bool = True,
):
    """
    Creates a PUT endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    update_schema - The update schema for the object (e.g. EventUpdate)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    admin_only (optional) - Set the API endpoint for admin users only (defaults to False)
    many (optional) - Create a many API endpoint as well to all for updating multiple objects at once
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    description = f"Update one or more fields of {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}"

    if admin_only:
        modify_dep = Depends(deps.admin_only)
        modify_many_dep = Depends(deps.admin_only)
        description += " (admins only)"
    else:
        modify_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.modify))
        modify_many_dep = Depends(deps.PermissionCheckIds(target_type, PermissionEnum.modify))

    description, examples = create_schema_details(update_schema, description)

    if many:
        many_description = f"Update one or more fields of more than one {pretty_name}"

        @router.put(
            "/many",
            response_model=list[response_schema],
            summary=f"Update many {pluralize_name(pretty_name)}",
            description=many_description,
            dependencies=[modify_many_dep],
        )
        def update_objects(
            *,
            db: Session = Depends(deps.get_db),
            audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
            current_user: models.User = Depends(deps.get_current_active_user),
            ids: Annotated[list[int], Query(...)],
            obj: Annotated[update_schema, Body(..., openapi_examples=examples, alias=pretty_name.lower())],  # type: ignore
            background_tasks: BackgroundTasks,
        ) -> Any:
            _objs = []
            for id in ids:
                _objs.append(update_object(db=db, audit_logger=audit_logger, current_user=current_user, id=id, obj=obj, background_tasks=background_tasks))

            return _objs

    @router.put(
        "/{id}",
        response_model=response_schema,
        summary=f"Update {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=description,
        dependencies=[modify_dep],
    )
    def update_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        current_user: models.User = Depends(deps.get_current_active_user),
        id: Annotated[int, Path(...)],
        obj: Annotated[update_schema, Body(..., openapi_examples=examples, alias=pretty_name.lower())],  # type: ignore
        background_tasks: BackgroundTasks,
    ) -> Any:
        _obj = crud_type.get(db, id)
        if not _obj:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")
        try:
            response_schema.model_validate(_obj)
        except ValidationError as e:
            raise HTTPException(422, f"Validation error: {e}")

        updated = crud_type.update(db, db_obj=_obj, obj_in=obj, audit_logger=audit_logger)

        if target_type == TargetTypeEnum.entry:
            background_tasks.add_task(send_flair_entry_request, target_type, updated)
        elif target_type == TargetTypeEnum.event:
            if obj.status == StatusEnum.closed:
                # need to add an MTTR for event closing
                _event_data = crud.event.get(
                    db_session=db,
                    _id=id,
                    audit_logger=audit_logger
                )

                _metric = schemas.SpecialMetricCreate(
                    target_id=id,
                    target_type=TargetTypeEnum.event,
                    metric_type=SpecialMetricEnum.mttr,
                    start_time=_event_data.created,
                    end_time=datetime.now(timezone.utc)
                )

                _metric_obj = crud.special_metric.get_or_create(
                    db_session=db,
                    obj_in=_metric,
                    audit_logger=audit_logger
                )
        crud.notification.send_update_notifications(db, updated, current_user, extra_data=obj.model_dump(exclude_unset=True))
        return updated


def generic_get(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    pretty_name: str | None = None,
    admin_only: bool = False,
):
    """
    Creates a GET endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    admin_only (optional) - Set the API endpoint for admin users only (defaults to False)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    description = f"Get a single {pretty_name} by id"
    if admin_only:
        read_dep = Depends(deps.admin_only)
        description += " (admins only)"
    else:
        read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id:int}",
        response_model=response_schema,
        summary=f"Get {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=description,
        dependencies=[read_dep],
    )
    def read_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Path(...)],
    ) -> Any:
        _obj = crud_type.get(db, id, audit_logger)
        if not _obj:
            raise HTTPException(404, f"{pretty_name} {id} not found")
        if hasattr(crud_type, "increment_view_count"):
            crud_type.increment_view_count(db_session=db, id=id)
        return _obj


def generic_delete(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    pretty_name: str | None = None,
    admin_only: bool = False,
    many: bool = True
):
    """
    Creates a DELETE endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    admin_only (optional) - Set the API endpoint for admin users only (defaults to False)
    many (optional) - Create a many API endpoint as well to all for deleting multiple objects at once
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    description = f"Delete {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}"

    if admin_only:
        delete_dep = Depends(deps.admin_only)
        delete_many_dep = Depends(deps.admin_only)
        description += " (admins only)"
    else:
        delete_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.delete))
        delete_many_dep = Depends(deps.PermissionCheckIds(target_type, PermissionEnum.delete))

    if many:
        many_description = f"Delete more than one {pretty_name}"

        @router.delete(
            "/many",
            response_model=list[response_schema],
            summary=f"Delete many {pluralize_name(pretty_name)}",
            description=many_description,
            dependencies=[delete_many_dep],
        )
        def delete_objects(
            *,
            db: Session = Depends(deps.get_db),
            audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
            ids: Annotated[list[int], Query(...)],
        ) -> Any:
            _objs = []
            for id in ids:
                _objs.append(delete_object(db=db, audit_logger=audit_logger, id=id))
            return _objs

    @router.delete(
        "/{id}",
        response_model=response_schema,
        summary=f"Delete {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=description,
        dependencies=[delete_dep],
    )
    def delete_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Path(...)],
    ) -> Any:
        _obj_group = crud_type.get(db, id)

        if not _obj_group:
            raise HTTPException(404, f"{pretty_name} not found")
        return crud_type.remove(db, _id=id, audit_logger=audit_logger)


def generic_undelete(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    pretty_name: str | None = None,
):
    """
    Creates an undelete endpoint on a router for the specified target type
    Should be created AFTER the corresponding POST endpoint, if there is one

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)

    @router.post(
        "/undelete",
        response_model=response_schema,
        summary=f"Undelete {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description="This will reverse the last recorded deletion of the object with the specified id by you. Only admins can undelete something that someone else has deleted.",
    )
    def undelete_object(
        *,
        target_id: Annotated[int, Query(...)],
        keep_ids: Annotated[bool, Query(...)] = True,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.get_current_active_user),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    ) -> Any:
        deleting_username = current_user.username
        if crud.permission.user_is_admin(db, current_user):
            deleting_username = None
        try:
            undeleted_obj = crud_type.undelete(db, target_id, None, keep_ids, deleting_username, audit_logger)
            if not undeleted_obj:
                raise HTTPException(404, f"Target deleted object with id {target_id} not found")
            return undeleted_obj
        except ValueError as e:
            raise HTTPException(422, str(e))


def generic_entries(
    router: APIRouter,
    target_type: TargetTypeEnum,
    pretty_name: str | None = None
):
    """
    Creates a GET endpoint on a router to get a specific item's entries

    args:
    router - The router to add the route to
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/entry",
        response_model=schemas.ListResponse[schemas.Entry],
        dependencies=[read_dep],
        description=f"Get the entries of a single {pretty_name} by id",
        summary=f"Get {pretty_name} entries",
    )
    def read_entries(
        *,
        id: Annotated[int, Path(...)],
        skip: Annotated[int, Query(...)] = 0,
        limit: Annotated[int, Query(...)] = 100,
        roles: list[models.Role] = Depends(deps.get_current_roles),
        db: Session = Depends(deps.get_db),
        _: deps.AuditLogger = Depends(deps.get_audit_logger),
    ) -> Any:
        if target_type in deps.PermissionCheck.type_allow_whitelist:
            roles = None  # We added this to not check roles if an element does not have permissions (like entities, tags, sources, etc.)
        _entries, count = crud.entry.get_by_type(db, roles=roles, _id=id, _type=target_type, skip=skip, limit=limit)
        return {"totalCount": count, "resultCount": len(_entries), "result": _entries}


def generic_files(
    router: APIRouter,
    target_type: TargetTypeEnum,
    pretty_name: str | None = None
):
    """
    Creates a GET endpoint on a router to get a specific item's entities

    args:
    router - The router to add the route to
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/files",
        response_model=schemas.ListResponse[schemas.File],
        dependencies=[read_dep],
        description=f"Get all the files of a single {pretty_name} by id",
        summary=f"Get {pretty_name} files",
    )
    def read_files(
        *,
        id: Annotated[int, Path(...)],
        roles: list[models.Role] = Depends(deps.get_current_roles),
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    ) -> Any:
        _files, count = crud.file.retrieve_element_files(db, id, target_type)
        return {"totalCount": count, "resultCount": len(_files), "result": _files}


def generic_entities(
    router: APIRouter,
    target_type: TargetTypeEnum,
    pretty_name: str | None = None
):
    """
    Creates a GET endpoint on a router to get a specific item's entities

    args:
    router - The router to add the route to
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/entity",
        response_model=schemas.ListResponse[schemas.Entity],
        dependencies=[read_dep],
        description=f"Get all the entities of a single {pretty_name} by id",
        summary=f"Get {pretty_name} entities",
    )
    def read_entities(
        *,
        id: Annotated[int, Path(...)],
        _: list[models.Role] = Depends(deps.get_current_roles),
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    ) -> Any:
        _entities, count = crud.entity.retrieve_element_entities(db, id, target_type)
        return {"totalCount": count, "resultCount": len(_entities), "result": _entities}


def generic_tag_untag(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    pretty_name: str | None = None,
):
    """
    Creates two POST endpoints on a router to tag/untag a specific target type
    Returns the object that was modified in either case
    For now, permissions on tags are ignored (do tag permissions even make sense?)

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)

    @router.post(
        "/{id}/tag",
        response_model=response_schema,
        summary=f"Tag {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Add a tag to {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}, either by name or by id, creating the tag by name if it does not already exist",
    )
    def tag_object(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        user: models.User = Depends(deps.get_current_active_user),
        roles: list[models.Role] = Depends(deps.get_current_roles),
        tag_id: Annotated[int | None, Body(alias="id", validation_alias="id")] = None,
        tag_name: Annotated[str | None, Body(alias="name", validation_alias="name")] = None,
    ) -> Any:
        item = crud_type.get(db, id, audit_logger=audit_logger)
        # Get effective permissions on target object
        if not item or not deps.PermissionCheckId(target_type, PermissionEnum.modify)(id, db, user, roles):
            raise HTTPException(404, f"{target_type.name.capitalize()} with id {id} does not exist, or you do not have modify permissions on it")
        if tag_id is not None:
            tag = crud.tag.assign(db, tag_id, target_type, id, audit_logger)
            if not tag:
                raise HTTPException(404, f"Tag with id {tag_id} not found")
        elif tag_name is not None:
            crud.tag.assign_by_name(db, tag_name, target_type, id, True, None, audit_logger)
        else:
            raise HTTPException(422, "You must specify either the name or id of the tag")
        db.refresh(item)
        return item

    @router.post(
        "/{id}/untag",
        response_model=response_schema,
        summary=f"Untag {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Remove a tag from a {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}, either by name or by id",
    )
    def untag_object(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        user: models.User = Depends(deps.get_current_active_user),
        roles: list[models.Role] = Depends(deps.get_current_roles),
        tag_id: Annotated[int | None, Body(alias="id", validation_alias="id")] = None,
        tag_name: Annotated[str | None, Body(alias="name", validation_alias="name")] = None,
    ) -> Any:
        item = crud_type.get(db, id)
        # Get effective permissions on target object
        if not item or not deps.PermissionCheckId(target_type, PermissionEnum.modify)(id, db, user, roles):
            raise HTTPException(404, f"{target_type.name.capitalize()} with id {id} does not exist, or you do not have modify permissions on it")
        if tag_id is not None:
            tag = crud.tag.unassign(db, tag_id, target_type, id, audit_logger)
            if not tag:
                raise HTTPException(422, f"{pretty_name.capitalize()} {id} does not have tag {tag_id}")
        elif tag_name is not None:
            tag = crud.tag.unassign_by_name(db, tag_name, target_type, id, audit_logger)
            if not tag:
                raise HTTPException(404, f"Tag '{tag_name}' does not exist")
        else:
            raise HTTPException(422, "You must specify either the name or id of the tag")
        db.refresh(item)
        return item


def generic_source_add_remove(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    pretty_name: str | None = None,
):
    """
    Creates two POST endpoints on a router to add/remove sources on a specific target type
    Returns the object that was modified in either case
    For now, permissions on sources are ignored (do source permissions even make sense?)

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)

    @router.post(
        "/{id}/add-source",
        response_model=response_schema,
        summary=f"Add source to {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Add a source to {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}, either by name or by id, creating the source by name if it does not already exist",
    )
    def object_add_source(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        user: models.User = Depends(deps.get_current_active_user),
        roles: list[models.Role] = Depends(deps.get_current_roles),
        source_id: Annotated[int | None, Body(alias="id", validation_alias="id")] = None,
        source_name: Annotated[str | None, Body(alias="name", validation_alias="name")] = None,
    ) -> Any:
        item = crud_type.get(db, id)
        # Get effective permissions on target object
        if not item or not deps.PermissionCheckId(target_type, PermissionEnum.modify)(id, db, user, roles):
            raise HTTPException(404, f"{target_type.name.capitalize()} with id {id} does not exist, or you do not have modify permissions on it")
        if source_id is not None:
            source = crud.source.assign(db, source_id, target_type, id, audit_logger)
            if not source:
                raise HTTPException(404, f"Source with id {source_id} not found")
        elif source_name is not None:
            crud.source.assign_by_name(db, source_name, target_type, id, True, None, audit_logger)
        else:
            raise HTTPException(422, "You must specify either the name or id of the source")
        db.refresh(item)
        return item

    @router.post(
        "/{id}/remove-source",
        response_model=response_schema,
        summary=f"Remove source from {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Remove a source from {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}, either by name or by id",
    )
    def object_remove_source(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        user: models.User = Depends(deps.get_current_active_user),
        roles: list[models.Role] = Depends(deps.get_current_roles),
        source_id: Annotated[int | None, Body(alias="id", validation_alias="id")] = None,
        source_name: Annotated[str | None, Body(alias="name", validation_alias="name")] = None,
    ) -> Any:
        item = crud_type.get(db, id)
        # Get effective permissions on target object
        if not item or not deps.PermissionCheckId(target_type, PermissionEnum.modify)(id, db, user, roles):
            raise HTTPException(404, f"{target_type.name.capitalize()} with id {id} does not exist, or you do not have modify permissions on it")
        if source_id is not None:
            source = crud.source.unassign(db, source_id, target_type, id, audit_logger)
            if not source:
                raise HTTPException(422, f"Source not found on {pretty_name} {id}")
        elif source_name is not None:
            source = crud.source.unassign_by_name(db, source_name, target_type, id, audit_logger)
            if not source:
                raise HTTPException(404, f"Source {source_name} does not exist")
        else:
            raise HTTPException(422, "You must specify either the name or id of the source")
        db.refresh(item)
        return item


def generic_history(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    pretty_name: str | None = None,
):
    """
    Creates a GET endpoint that gets all audit entries associated with an
    object. Unlike other audit endpoints, users can see the entries of other
    users, however they must have read permissions on the object.

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/history",
        response_model=list[schemas.Audit],
        summary=f"Get the audit history of {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Get the audit entries of {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}. Read audit entries are limited to the latest read done by each user.",
        dependencies=[read_dep],
    )
    def object_history(
        *,
        db: Session = Depends(deps.get_db),
        id: Annotated[int, Path(...)],
    ):
        result = crud_type.get_history(db, id)
        if pretty_name in ['event', 'incident', 'intel', 'product', 'alertgroup']:
            _obj = crud_type.get(db, id)
            if not _obj:
                return result
            sub_crud_type = crud.alert if pretty_name == 'alertgroup' else crud.entry
            sub_collection = _obj.alerts if pretty_name == 'alertgroup' else _obj.entries
            for subItem in sub_collection:
                subResult = sub_crud_type.get_history(db, subItem.id)
                for audit in subResult:
                    if audit.thing_type in ['entry', 'alert']\
                            and audit.what in ['create', 'delete', 'update']:
                        result.append(audit)
        return result


def generic_reflair(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    pretty_name: str | None = None,
):
    """
    Creates a GET endpoint on a router for the specified target type that requests a
    reflair of an item

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/reflair",
        response_model=response_schema,
        summary=f"Reflair {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Reflair a single {pretty_name} by id",
        dependencies=[read_dep],
    )
    def reflair_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Path(...)],
        background_tasks: BackgroundTasks,
    ) -> Any:
        _obj = crud_type.get(db, id, audit_logger)
        if _obj is None:
            raise HTTPException(404, f"{pretty_name} not found")
        if target_type == TargetTypeEnum.entry and _obj.entry_class == EntryClassEnum.promotion:
            # promoted entry is an event->incident
            if _obj.target_type == TargetTypeEnum.incident:
                for source in _obj.entry_data.get('promotion_sources', []):
                    if source['type'] == "event":
                        _obj2 = crud.event.get(db, source['id'])
                        for entry in _obj2.entries:
                            background_tasks.add_task(send_reflair_request, entry.id, TargetTypeEnum.entry, entry.entry_data["html"])
            # promoted entry is an alert->event
            elif _obj.target_type == TargetTypeEnum.event:
                _obj2 = crud.event.get(db, _obj.target_id)
                if _obj2 is not None:
                    for source in _obj2.promoted_from_sources:
                        if source.p0_type == TargetTypeEnum.alert:
                            _obj3 = crud.alert.get(db, source.p0_id)
                            _obj4 = crud.alert_group.get(db, _obj3.alertgroup_id)
                            background_tasks.add_task(send_reflair_request, _obj4.id, TargetTypeEnum.alertgroup, {"alerts": [{"id": a.id, "row": dict(a.data)} for a in _obj4.alerts]})
            # promoted entry is a dispatch->intel
            elif _obj.target_type == TargetTypeEnum.intel:
                for prom_source in _obj.entry_data.get("promotion_sources", []):
                    if prom_source["type"] == "dispatch":
                        dispatch_id = prom_source["id"]
                        _obj2 = crud.dispatch.get(db_session=db, _id=dispatch_id)
                        for entry in _obj2.entries:
                            background_tasks.add_task(send_reflair_request, entry.id, TargetTypeEnum.entry, entry.entry_data["html"])
        if target_type == TargetTypeEnum.entry and _obj.entry_class != EntryClassEnum.promotion:
            background_tasks.add_task(send_reflair_request, _obj.id, TargetTypeEnum.entry, _obj.entry_data["html"])
        if target_type == TargetTypeEnum.alertgroup:
            background_tasks.add_task(send_reflair_request, _obj.id, TargetTypeEnum.alertgroup, {"alerts": [{"id": a.id, "row": dict(a.data)} for a in _obj.alerts]})
        return _obj


def generic_search(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    search_schema_base: SearchBase,
    response_schema: BaseModel,
    pretty_name: str | None = None,
    user_only: bool = False,
):
    """
    Creates a GET endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    response_schema - The standard search object schema for the object (e.g. EventSearch)
    response_schema - The standard object schema for the object (e.g. Event)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    user_only (optional) - Return only user owned items unless user is an admin
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)

    @router.get(
        "/",
        response_model=schemas.ListResponse[response_schema],
        summary=f"Search {pluralize_name(pretty_name)}",
    )
    def search_object(
        *,
        db: Session = Depends(deps.get_db),
        roles: list[models.Role] = Depends(deps.get_current_roles),
        current_user: models.User = Depends(deps.get_current_active_user),
        skip: Annotated[int, Query(...)] = 0,
        limit: Annotated[int, Query(...)] = 100,
        sort: Annotated[str | SkipJsonSchema[None], Query(...)] = None,
        search_schema: search_schema_base = Depends()  # type: ignore
    ) -> Any:
        """
        ### Perform a paginated search, optionally filtering on one or more available fields
        Only results that match all filters will be returned. The filters can be modified
        using the syntax below.
        | | |
        | --- | --- |
        | `!` | return the opposite result |
        | `(n, n1)` | select values within the given range |
        | `!(n, n1)` | select values **NOT** within the given range |
        | `[n, n1, n2, ...]` | select multiple values within a list |
        | `![n, n1, n2, ...]` | select **NOT** multiple values within a list |
        | `\\` | use a backslash to escape a special character at the beginning of your search string; you must escape a starting parenthesis `(`, bracket `[`, or exclamation point `!` or it will be interpreted as above |

        ### Examples:
        | | |
        | --- | --- |
        | `id=1` | return all items with ids that match the value |
        | `id=!1` | return all items with ids that don't match the value |
        | `modified=(2024-01-01, 2024-01-02)` | return all items last modified between the dates |
        | `modified=!(2024-01-01, 2024-01-02)` | return all items that were not last modified between the dates |
        | `owner=[alice, bob]` | return all items that have any of the listed owners |
        | `owner=![charlie, dave]` | return all items that don't have any of the listed owners |
        | `name=\\!test` | return all items with names that match including the `!`, but not including the `\\`|
        | `name=\\(test)` | return all items with names that match including the `(` and `)`, but not including the `\\` |

        ### Notes:
        - Non-numeric/non-date fields can't use the range filters, for example `subject` or `description`. If range filters are provided the system will treat them as a list filter instead.
        - If none of the range or list filters work it will attempt to do a normal search
        - Datetimes are parsed using the [dateutil module](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse)
        - Some fields (e.g. event subjects and entity values) default to "contains" string searches, where any item containing the searched string will match (so searching for `example.com` would match both `example.com` and `foo.example.com`). Searching these fields with list searches (with square brackets) disables this feature for all list items, but "range" searches (with parentheses) search normally. For example, searching `[example.com]` wouldn't match `foo.example.com` but searching `(example.com)` would match.
        """

        if target_type in deps.PermissionCheck.type_allow_whitelist:
            # If on the whitelist, don't check permissions when searching
            roles = None

        try:
            filter_dict = get_search_filters(search_schema)
            if user_only and not crud.permission.user_is_admin(db, current_user):
                filter_dict["username"] = current_user.username
            _result, _count = crud_type.query_with_filters(db, roles, filter_dict, sort, skip, limit)
        except ValueError as e:
            raise HTTPException(422, str(e))

        return {"totalCount": _count, "resultCount": len(_result), "result": _result}


def generic_export(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    pretty_name: str | None = None,
):
    """
    Creates a GET endpoint on a router that exports an item of the given target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)
    description = f"Export {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name} and associated entries to one of the available formats"

    def remove_file(file: str) -> None:
        os.remove(file)

    @router.get(
        "/export",
        response_model=Any,
        summary=f"Export {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=description,
    )
    def export(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Query(...)],
        format: Annotated[ExportFormatEnum, Query(...)] = ExportFormatEnum.html,
        background_tasks: BackgroundTasks
    ) -> Any:
        # get original object
        _obj = crud_type.get(db_session=db, _id=id, audit_logger=audit_logger)
        if not _obj:
            raise HTTPException(404, f"{pretty_name} {id} not found")

        tmp_file, media_type = export_object(db, _obj, target_type, format, pretty_name)
        # add a background task to remove the temporary file after it has been sent
        background_tasks.add_task(remove_file, tmp_file)
        return FileResponse(
            tmp_file,
            media_type=media_type,
            filename=f"{quote(target_type.value)}_{_obj.id}.{quote(format.value)}",
        )


def generic_upvote_and_downvote(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    pretty_name: str | None = None,
):
    """
    Creates two POST endpoints on a router to upvote/downvote on a specific target type
    Returns the object that was modified in either case
    For now, permissions on sources are ignored (do source permissions even make sense?)

    args:
    router - The router to add the route to
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)

    @router.post(
        "/{id}/upvote",
        response_model=response_schema,
        summary=f"Add an upvote to {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Add an upvote to {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}, creating a popularity record for the user if it does not already exist.",
    )
    def object_upvote(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_user),
    ) -> Any:
        item = crud_type.get(db, id)
        if not item:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")

        popularity = crud.popularity.get_user_metric(db, target_type, id, user.id)
        # if upvote exists
        if popularity:
            # if popularity is downvote update to upvote
            if popularity.metric_type == PopularityMetricEnum.downvote:
                popularity_obj = schemas.PopularityUpdate(
                    metric_type=PopularityMetricEnum.upvote
                )
                crud.popularity.update(db, db_obj=popularity, obj_in=popularity_obj)
            # if popularity is upvote delete
            else:
                crud.popularity.remove(db, _id=popularity.id)
        # if upvote does not exist create
        else:
            popularity_obj = schemas.PopularityCreate(
                target_id=id,
                target_type=target_type,
                metric_type=PopularityMetricEnum.upvote,
                owner_id=user.id
            )
            crud.popularity.create(db, obj_in=popularity_obj)

        db.refresh(item)
        return item

    @router.post(
        "/{id}/downvote",
        response_model=response_schema,
        summary=f"Add a downvote to {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Add a downvote to {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}, creating a popularity record for the user if it does not already exist.",
    )
    def object_downvote(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_user),
    ) -> Any:
        item = crud_type.get(db, id)
        if not item:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")

        popularity = crud.popularity.get_user_metric(db, target_type, id, user.id)
        # if downvote exists
        if popularity:
            # if popularity is upvote update to downvote
            if popularity.metric_type == PopularityMetricEnum.upvote:
                popularity_obj = schemas.PopularityUpdate(
                    metric_type=PopularityMetricEnum.downvote
                )
                crud.popularity.update(db, db_obj=popularity, obj_in=popularity_obj)
            # if popularity is downvote delete
            else:
                crud.popularity.remove(db, _id=popularity.id)
        # if downvote does not exist create
        else:
            popularity_obj = schemas.PopularityCreate(
                target_id=id,
                target_type=target_type,
                metric_type=PopularityMetricEnum.downvote,
                owner_id=user.id
            )
            crud.popularity.create(db, obj_in=popularity_obj)

        db.refresh(item)
        return item


def generic_user_links(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    pretty_name: str | None = None,
):
    """
    Creates a POST endpoint on a router to favorite/unfavorite on a specific target type
    Returns the object that was modified in either case
    For now, permissions on sources are ignored (do source permissions even make sense?)

    args:
    router - The router to add the route to
    target_type - The TargetTypeEnum object that refers to these objects (or None if there is no TargetTypeEnum entry)
    pretty_name (optional) - A user-friendly name for this type of object (defaults to the string of the target type)
    """
    pretty_name = gen_pretty_name(pretty_name, target_type)

    @router.post(
        "/{id}/favorite",
        response_model=response_schema,
        summary=f"Toggle favorite status of {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}",
        description=f"Favorite {'an' if pretty_name.lower()[0] in 'aeiou' else 'a'} {pretty_name}, creating the user link entry if it does not already exist; if it does exist it will unfavorite the {pretty_name}.",
    )
    def object_favorite(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        user: models.User = Depends(deps.get_current_active_user),
    ) -> Any:
        item = crud_type.get(db, id)
        if not item:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")

        user_favorite = crud.user_links.get_favorite(db, id, target_type, user.id)

        # if favorite exists delete it
        if user_favorite:
            crud.user_links.remove(db, _id=user_favorite.id)
        # if favorite does not exist create
        else:
            user_links_obj = schemas.UserLinksCreate(
                link_type=UserLinkEnum.favorite,
                target_id=id,
                target_type=target_type,
                owner_id=user.id
            )
            crud.user_links.create(db, obj_in=user_links_obj)

        db.refresh(item)
        return item
