import os
import uuid
import json

from pydantic import BaseModel, ValidationError, create_model, Field
from pydantic.json_schema import SkipJsonSchema
from typing import Any, Union, Annotated
from fastapi import BackgroundTasks, Body, Depends, HTTPException, APIRouter, Path, Query
from sqlalchemy.orm import Session
from urllib.parse import quote
from fastapi.responses import FileResponse
from tabulate import tabulate
from tempfile import gettempdir
from markdownify import markdownify
from xhtml2pdf import pisa
from pdf2docx import Converter

from app import crud, models, schemas
from app.crud.base import CRUDBase
from app.api import deps
from app.schemas.response import SearchBase
from app.schemas.permission import PermissionList
from app.enums import PermissionEnum, TargetTypeEnum, EntryClassEnum, ExportFormatEnum
from app.utils import send_flair_entry_request, send_reflair_request, create_schema_details


def generic_post(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    create_schema: BaseModel,
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None,
    admin_only: bool = False
):
    """
    Creates a POST endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    create_schema - The create schema for the object (e.g. EventCreate)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    # "Legacy" format where there's a top-level item key
    def GenLegacyFormat(name, model):
        if not name:
            return object
        return create_model('LegacyFormat', **{name: (SkipJsonSchema[model | None], Field(None, exclude=True))})

    # create a dummy schema that can handle permissions and the legacy creation format
    class PostObject(create_schema, PermissionList, GenLegacyFormat(target_type.value, create_schema)):
        pass

    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Create a {pretty_name}, optionally granting read, write, or delete permissions"
        if pretty_name.lower()[0] in "aeiou":
            description = description.replace(" a ", " an ")
    if summary is None:
        summary = f"Create a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    if admin_only:
        dependencies = [Depends(deps.admin_only)]
        description += " (admins only)"
    else:
        dependencies = []

    extra_description, examples = create_schema_details(PostObject)
    description += extra_description

    @router.post(
        "/",
        response_model=response_schema,
        summary=summary,
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
        permissions = obj.permissions
        del obj.permissions
        # if there is a legacy object key, use that instead of the actual object
        if target_type.value:
            if getattr(obj, target_type.value, None) is not None:
                obj = getattr(obj, target_type.value)
            elif hasattr(obj, target_type.value):
                delattr(obj, target_type.value)

        if target_type == TargetTypeEnum.none:
            _obj = crud_type.create(
                db_session=db, obj_in=obj, audit_logger=audit_logger
            )

        elif permissions is not None:
            _obj = crud_type.create_with_permissions(
                db_session=db,
                obj_in=obj,
                perm_in=permissions,
                audit_logger=audit_logger,
            )
        else:
            _obj = crud_type.create_with_owner(
                db_session=db, obj_in=obj, owner=current_user, audit_logger=audit_logger
            )
        if target_type == TargetTypeEnum.entry:
            obj_to_flair = _obj.entry_data["html"]
            background_tasks.add_task(
                send_reflair_request, _obj.id, TargetTypeEnum.entry, obj_to_flair
            )
        if target_type == TargetTypeEnum.alertgroup:
            obj_to_flair = {
                "alerts": [{"id": a.id, "row": dict(a.data)} for a in _obj.alerts]
            }
            background_tasks.add_task(
                send_reflair_request, _obj.id, TargetTypeEnum.alertgroup, obj_to_flair
            )
        if target_type == TargetTypeEnum.remote_flair:
            background_tasks.add_task(
                send_reflair_request, _obj.id, TargetTypeEnum.remote_flair, _obj.html
            )

        return _obj


def generic_put(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    update_schema: BaseModel,
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None,
    admin_only: bool = False,
):
    """
    Creates a PUT endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    update_schema - The update schema for the object (e.g. EventUpdate)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Update one or more fields of a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            description = description.replace(" a ", " an ")
    if summary is None:
        summary = f"Update a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    if admin_only:
        modify_dep = Depends(deps.admin_only)
        description += " (admins only)"
    else:
        modify_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.modify))

    extra_description, examples = create_schema_details(update_schema)
    description += extra_description

    @router.put(
        "/{id}",
        response_model=response_schema,
        summary=summary,
        description=description,
        dependencies=[modify_dep],
    )
    def update_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Path(...)],
        obj: Annotated[update_schema, Body(..., openapi_examples=examples, alias=pretty_name.lower())],
        background_tasks: BackgroundTasks,
    ) -> Any:
        _obj = crud_type.get(db_session=db, _id=id)
        if not _obj:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")
        try: 
            response_schema.model_validate(_obj)
        except ValidationError as e:
            raise HTTPException(422, f"Validation error: {e}")

        updated = crud_type.update(
            db_session=db, db_obj=_obj, obj_in=obj, audit_logger=audit_logger
        )

        if target_type == TargetTypeEnum.entry:
            background_tasks.add_task(
                send_flair_entry_request, target_type, updated
            )
        return updated


def generic_get(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None,
):
    """
    Creates a GET endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Get a single {pretty_name} by id"
    if summary is None:
        summary = f"Get a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}",
        response_model=response_schema,
        summary=summary,
        description=description,
        dependencies=[read_dep],
    )
    def read_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Path(...)],
    ) -> Any:
        _obj = crud_type.get(db_session=db, _id=id, audit_logger=audit_logger)
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
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None,
    admin_only: bool = False,
):
    """
    Creates a DELETE endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Delete a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            description = description.replace(" a ", " an ")
    if summary is None:
        summary = f"Delete a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    if admin_only:
        delete_dep = Depends(deps.admin_only)
        description += " (admins only)"
    else:
        delete_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.delete))

    @router.delete(
        "/{id}",
        response_model=response_schema,
        summary=summary,
        description=description,
        dependencies=[delete_dep],
    )
    def delete_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Path(...)],
    ) -> Any:
        _obj_group = crud_type.get(db_session=db, _id=id)

        if not _obj_group:
            raise HTTPException(404, f"{pretty_name} not found")
        deleted = crud_type.remove(db_session=db, _id=id, audit_logger=audit_logger)
        return deleted


def generic_undelete(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    summary: str | None = None,
    description: str | None = None,
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
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = (
            "This will reverse the last recorded deletion of the "
            "object with the specified id by you. Only admins can "
            "undelete something that someone else has deleted."
        )
        if pretty_name.lower()[0] in "aeiou":
            description = description.replace(" a ", " an ")
    if summary is None:
        summary = f"Undelete a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    @router.post(
        "/undelete",
        response_model=response_schema,
        summary=summary,
        description=description,
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
            undeleted_obj = crud_type.undelete(
                db,
                target_id=target_id,
                keep_ids=keep_ids,
                by_user=deleting_username,
                audit_logger=audit_logger,
            )
            if not undeleted_obj:
                raise HTTPException(404, f"Target deleted object with id {target_id} not found")
            return undeleted_obj
        except ValueError as e:
            raise HTTPException(422, str(e))


def generic_entries(
    router: APIRouter,
    target_type: TargetTypeEnum,
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None
):
    """
    Creates a GET endpoint on a router to get a specific item's entries

    args:
    router - The router to add the route to
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Get all the entries of a single {pretty_name} by id"
    if summary is None:
        summary = f"Get {pretty_name} entries"

    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/entry",
        response_model=schemas.ListResponse[schemas.Entry],
        dependencies=[read_dep],
        description=description,
        summary=summary,
    )
    def read_entries(
        *,
        id: Annotated[int, Path(...)],
        skip: Annotated[int, Query(...)] = 0,
        limit: Annotated[int, Query(...)] = 100,
        roles: list[models.Role] = Depends(deps.get_current_roles),
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    ) -> Any:
        if target_type in deps.PermissionCheck.type_allow_whitelist:
            roles = None  # We added this to not check roles if an element does not have permissions (like entities, tags, sources, etc.)
        _entries, count = crud.entry.get_by_type(
            db_session=db,
            roles=roles,
            _id=id,
            _type=target_type,
            skip=skip,
            limit=limit,
        )
        return {"totalCount": count, "resultCount": len(_entries), "result": _entries}


def generic_files(
    router: APIRouter,
    target_type: TargetTypeEnum,
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None
):
    """
    Creates a GET endpoint on a router to get a specific item's entities

    args:
    router - The router to add the route to
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Get all the files of a single {pretty_name} by id"
    if summary is None:
        summary = f"Get {pretty_name} files"

    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/files",
        response_model=schemas.ListResponse[schemas.File],
        dependencies=[read_dep],
        description=description,
        summary=summary,
    )
    def read_files(
        *,
        id: Annotated[int, Path(...)],
        roles: list[models.Role] = Depends(deps.get_current_roles),
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    ) -> Any:
        _files, count = crud.file.retrieve_element_files(
            db_session=db, source_id=id, source_type=target_type
        )
        return {"totalCount": count, "resultCount": len(_files), "result": _files}


def generic_entities(
    router: APIRouter,
    target_type: TargetTypeEnum,
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None
):
    """
    Creates a GET endpoint on a router to get a specific item's entities

    args:
    router - The router to add the route to
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Get all the entities of a single {pretty_name} by id"
    if summary is None:
        summary = f"Get {pretty_name} entities"

    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/entity",
        response_model=schemas.ListResponse[schemas.Entity],
        dependencies=[read_dep],
        description=description,
        summary=summary,
    )
    def read_entities(
        *,
        id: Annotated[int, Path(...)],
        roles: list[models.Role] = Depends(deps.get_current_roles),
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    ) -> Any:
        _entities, count = crud.entity.retrieve_element_entities(
            db_session=db, source_id=id, source_type=target_type
        )
        return {"totalCount": count, "resultCount": len(_entities), "result": _entities}


def generic_tag_untag(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    summary_tag: str | None = None,
    summary_untag: str | None = None,
    description_tag: str | None = None,
    description_untag: str | None = None,
    pretty_name: str | None = None,
):
    """
    Creates two POST endpoints on a router to tag/untag a specific target type
    Returns the object that was modified in either case
    For now, permissions on tags are ignored (do tag permissions even
        make sense?)

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    summary_tag (optional) - The summary to put in the documentation for the
                            tag endpoint
    summary_untag (optional) - The summary to put in the documentation for the
                            untag endpoint
    description_tag (optional) - The description to put in the documentation for
                            the tag endpoint
    description_untag (optional) - The description to put in the documentation
                            for the untag endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description_tag is None:
        description_tag = f"Add a tag to a specific {pretty_name}, creating the tag if it does not already exist"
    if description_untag is None:
        description_untag = f"Remove a tag from a specific {pretty_name}"
    if summary_tag is None:
        summary_tag = f"Tag a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary_tag = summary_tag.replace(" a ", " an ")
    if summary_untag is None:
        summary_untag = f"Untag a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary_untag = summary_untag.replace(" a ", " an ")

    @router.post(
        "/{id}/tag",
        response_model=response_schema,
        summary=summary_tag,
        description=description_tag,
    )
    def tag_object(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        current_roles: models.User = Depends(deps.get_current_roles),
        tag_id: Annotated[int | None, Body(alias="id")] = None,
        tag_name: Annotated[str | None, Body(alias="name")] = None,
    ) -> Any:
        item = crud_type.get(db, id)
        if not item:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")
        if tag_id is not None:
            tag = crud.tag.assign(
                db,
                tag_id=tag_id,
                target_type=target_type,
                target_id=id,
                audit_logger=audit_logger,
            )
            if not tag:
                raise HTTPException(404, f"Tag with id {tag_id} not found")
        elif tag_name is not None:
            crud.tag.assign_by_name(
                db,
                tag_name=tag_name,
                target_type=target_type,
                target_id=id,
                create=True,
                audit_logger=audit_logger,
            )
        else:
            raise HTTPException(422, "You must specify either the name or id of the tag")
        db.refresh(item)
        return item

    @router.post(
        "/{id}/untag",
        response_model=response_schema,
        summary=summary_untag,
        description=description_untag,
    )
    def untag_object(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        current_roles: models.User = Depends(deps.get_current_roles),
        tag_id: Annotated[int | None, Body(alias="id")] = None,
        tag_name: Annotated[str | None, Body(alias="name")] = None,
    ) -> Any:
        item = crud_type.get(db, id)
        if not item:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")
        if tag_id is not None:
            tag = crud.tag.unassign(
                db,
                tag_id=tag_id,
                target_type=target_type,
                target_id=id,
                audit_logger=audit_logger,
            )
            if not tag:
                raise HTTPException(422, f"{pretty_name.capitalize()} {id} does not have tag {tag_id}")
        elif tag_name is not None:
            tag = crud.tag.unassign_by_name(
                db,
                tag_name=tag_name,
                target_type=target_type,
                target_id=id,
                audit_logger=audit_logger,
            )
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
    summary_add: str | None = None,
    summary_remove: str | None = None,
    description_add: str | None = None,
    description_remove: str | None = None,
    pretty_name: str | None = None,
):
    """
    Creates two POST endpoints on a router to add/remove sources on a specific
        target type
    Returns the object that was modified in either case
    For now, permissions on sources are ignored (do source permissions even
        make sense?)

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    summary_add (optional) - The summary to put in the documentation for the
                            add endpoint
    summary_remove (optional) - The summary to put in the documentation for the
                            remove endpoint
    description_add (optional) - The description to put in the documentation for
                            the add endpoint
    description_remove (optional) - The description to put in the documentation
                            for the remove endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description_add is None:
        description_add = f"Add a source to a specific {pretty_name}, creating the source if it does not already exist"
    if description_remove is None:
        description_remove = f"Remove a source from a specific {pretty_name}"
    if summary_add is None:
        summary_add = f"Add source to a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary_add = summary_add.replace(" a ", " an ")
    if summary_remove is None:
        summary_remove = f"Remove source from a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary_remove = summary_remove.replace(" a ", " an ")

    @router.post(
        "/{id}/add-source",
        response_model=response_schema,
        summary=summary_add,
        description=description_add,
    )
    def object_add_source(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        current_roles: models.User = Depends(deps.get_current_roles),
        source_id: Annotated[int | None, Body(alias="id")] = None,
        source_name: Annotated[str | None, Body(alias="name")] = None,
    ) -> Any:
        item = crud_type.get(db, id)
        if not item:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")
        if source_id is not None:
            source = crud.source.assign(
                db,
                source_id=source_id,
                target_type=target_type,
                target_id=id,
                audit_logger=audit_logger,
            )
            if not source:
                raise HTTPException(404, f"Source with id {source_id} not found")
        elif source_name is not None:
            crud.source.assign_by_name(
                db,
                source_name=source_name,
                target_type=target_type,
                target_id=id,
                create=True,
                audit_logger=audit_logger,
            )
        else:
            raise HTTPException(422, "You must specify either the name or id of the source")
        db.refresh(item)
        return item

    @router.post(
        "/{id}/remove-source",
        response_model=response_schema,
        summary=summary_remove,
        description=description_remove,
    )
    def object_remove_source(
        *,
        id: Annotated[int, Path(...)],
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        current_roles: models.User = Depends(deps.get_current_roles),
        source_id: Annotated[int | None, Body(alias="id")] = None,
        source_name: Annotated[str | None, Body(alias="name")] = None,
    ) -> Any:
        item = crud_type.get(db, id)
        if not item:
            raise HTTPException(404, f"{pretty_name.capitalize()} not found")
        if source_id is not None:
            source = crud.source.unassign(
                db,
                source_id=source_id,
                target_type=target_type,
                target_id=id,
                audit_logger=audit_logger,
            )
            if not source:
                raise HTTPException(422, f"Source not found on {pretty_name} {id}")
        elif source_name is not None:
            source = crud.source.unassign_by_name(
                db,
                source_name=source_name,
                target_type=target_type,
                target_id=id,
                audit_logger=audit_logger,
            )
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
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None,
):
    """
    Creates a GET endpoint that gets all audit entries associated with an
        object. Unlike other audit endpoints, users can see the entries of other
        users, however they must have read permissions on the object.

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    summary (optional) - The summary to put in the documentation for the
                            endpoint
    description (optional) - The description to put in the documentation
                            for the endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Get the audit entries of a specific {pretty_name}. Read audit entries are limited to the latest read done by each user."
    if summary is None:
        summary = f"Get the audit history of a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/history",
        response_model=list[schemas.Audit],
        summary=summary,
        description=description,
        dependencies=[read_dep],
    )
    def object_history(
        *,
        db: Session = Depends(deps.get_db),
        id: Annotated[int, Path(...)],
    ):
        result = crud_type.get_history(db, id)
        if pretty_name in ['event', 'incident', 'intel', 'product']:
            _obj = crud_type.get(db_session=db, _id=id, audit_logger=None)
            if not _obj:
                # raise HTTPException(status_code=404, detail="%s not found" % pretty_name)
                return result
            entry_crud_type = crud.entry
            for entry in _obj.entries:
                subResult = entry_crud_type.get_history(db, entry.id)
                for audit in subResult:
                    if audit.thing_type == "entry" and audit.what in ["create", "delete"]:
                        result.append(audit)
        return result


def generic_reflair(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    response_schema: BaseModel,
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None,
):
    """
    Creates a GET endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard object schema for the object (e.g. Event)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Reflair a single {pretty_name} by id"
    if summary is None:
        summary = f"Reflair a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    read_dep = Depends(deps.PermissionCheckId(target_type, PermissionEnum.read))

    @router.get(
        "/{id}/reflair",
        response_model=response_schema,
        summary=summary,
        description=description,
        dependencies=[read_dep],

    )
    def reflair_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Path(...)],
        background_tasks: BackgroundTasks,
    ) -> Any:
        _obj = crud_type.get(db_session=db, _id=id, audit_logger=audit_logger)
        if _obj is None:
            raise HTTPException(404, f"{pretty_name} not found")
        if target_type == TargetTypeEnum.entry and _obj.entry_class == EntryClassEnum.promotion:
            # promoted entry is an event->incident
            if _obj.target_type == TargetTypeEnum.incident:
                for source in _obj.entry_data.get('promotion_sources', []):
                    if source['type'] == "event":
                        _obj2 = crud.event.get(db_session=db, _id=source['id'])
                        for entry in _obj2.entries:
                            obj_to_flair = entry.entry_data["html"]
                            background_tasks.add_task(
                                send_reflair_request, entry.id, TargetTypeEnum.entry, obj_to_flair
                            )
            # promoted entry is an alert->event
            elif _obj.target_type == TargetTypeEnum.event:
                _obj2 = crud.event.get(db_session=db, _id=_obj.target_id)
                if _obj2 is not None:
                    for source in _obj2.promoted_from_sources:
                        if source.p0_type == TargetTypeEnum.alert:
                            _obj3 = crud.alert.get(db_session=db, _id=source.p0_id)
                            _obj4 = crud.alert_group.get(db_session=db, _id=_obj3.alertgroup_id)
                            obj_to_flair = {
                                "alerts": [{"id": a.id, "row": dict(a.data)} for a in _obj4.alerts]
                            }
                            background_tasks.add_task(
                                send_reflair_request, _obj4.id, TargetTypeEnum.alertgroup, obj_to_flair
                            )
            # promoted entry is a dispatch->intel
            elif _obj.target_type == TargetTypeEnum.intel:
                for prom_source in _obj.entry_data.get("promotion_sources", []):
                    if prom_source["type"] == "dispatch":
                        dispatch_id = prom_source["id"]
                        _obj2 = crud.dispatch.get(db_session=db, _id=dispatch_id)
                        for entry in _obj2.entries:
                            obj_to_flair = entry.entry_data["html"]
                            background_tasks.add_task(
                                send_reflair_request, entry.id, TargetTypeEnum.entry, obj_to_flair
                            )
        if target_type == TargetTypeEnum.entry and _obj.entry_class != EntryClassEnum.promotion:
            obj_to_flair = _obj.entry_data["html"]
            background_tasks.add_task(
                send_reflair_request, _obj.id, TargetTypeEnum.entry, obj_to_flair
            )
        if target_type == TargetTypeEnum.alertgroup:
            obj_to_flair = {
                "alerts": [{"id": a.id, "row": dict(a.data)} for a in _obj.alerts]
            }
            background_tasks.add_task(
                send_reflair_request, _obj.id, TargetTypeEnum.alertgroup, obj_to_flair
            )
        return _obj


def generic_search(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    search_schema_base: SearchBase,
    response_schema: BaseModel,
    summary: str | None = None,
    pretty_name: str | None = None,
):
    """
    Creates a GET endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    response_schema - The standard search object schema for the object (e.g. EventSearch)
    response_schema - The standard object schema for the object (e.g. Event)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type.value != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if summary is None:
        summary = f"Search {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    @router.get(
        "/",
        response_model=schemas.ListResponse[response_schema],
        summary=summary,
    )
    def search_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        roles: list[models.Role] = Depends(deps.get_current_roles),
        skip: Annotated[int | None, Query(...)] = 0,
        limit: Annotated[int | None, Query(...)] = 100,
        sort: Annotated[str | None, Query(...)] = None,
        search_schema: search_schema_base = Depends()
    ) -> dict:
        """
        ### Search using the available fields with the optional filters:
        - `!` - return the opposite result
        - `(n, n1)` - select values within the given range
        - `!(n, n1)` - select values **NOT** within the given range
        - `[n, n1, n2, ...]` - select multiple values with a list
        - `![n, n1, n2, ...]` - select multiple values **NOT** with a list
        - `\\` - use backslash to escape a special character please note that you must escape the starting parentheses `(` or the bracket `[`

        ### Examples:
        - `id=!1` - return all ids that don't match the value
        - `modified=('2024-01-01', '2024-01-02)` - return all values between the dates
        - `modified=!('2024-01-01', '2024-01-02)` - return all values that are not between the dates
        - `created=['2024-01-01', '2024-01-02', '2024-01-04']` - return all values that have any of the created dates
        - `created=!['2024-01-01', '2024-01-02', '2024-01-04']` - return all values that don't have any of the created dates
        - `name=\\!test` - return all names that match including the `!`
        - `name=\\(test) - return all names that match including the `(` and `)`

        ### Note:
        - Some fields can't use  the range filters, for example `subject` or `description`. If range filters are provided the system will treat them as a list filter instead.
        - If none of the range or list filters work it will attempt to do a normal search
        """

        filter_dict = {
            "not": {}
        }
        key: str
        value: str
        for key, value in search_schema.model_dump().items():
            if value is None:
                continue

            try:
                # remove any extra whitespace
                value = value.strip()
                do_normal = False
                # !(n, n1) - not in range
                if value.startswith("!(") and value.endswith(")"):
                    try:
                        # if for any reason this fails
                        v0, v1 = value[2:-1].split(",")
                    except Exception:
                        do_normal = True
                    else:
                        filter_dict["not"][key] = (search_schema.type_mapping(key, v0.strip()), search_schema.type_mapping(key, v1.strip()))
                # (n, n1) - range between two items i.e. ids, datetimes
                elif value.startswith("(") and value.endswith(")"):
                    try:
                        v0, v1 = value[1:-1].split(",")
                    except Exception:
                        do_normal = True
                    else:
                        filter_dict[key] = (search_schema.type_mapping(key, v0.strip()), search_schema.type_mapping(key, v1.strip()))
                # ![n, n1, n2, ...] - not in list of items
                elif value.startswith("![") and value.endswith("]"):
                    try:
                        v = value[2:-1].split(",")
                    except Exception:
                        do_normal = True
                    else:
                        filter_dict["not"][key] = [search_schema.type_mapping(key, a.strip()) for a in v]
                # [n, n1, n2, ...] - list of items
                elif value.startswith("[") and value.endswith("]"):
                    try:
                        v = value[1:-1].split(",")
                    except Exception:
                        do_normal = True
                    else:
                        filter_dict[key] = [search_schema.type_mapping(key, a.strip()) for a in v]
                # !n - not an item
                elif value.startswith("!"):
                    filter_dict["not"][key] = search_schema.type_mapping(key, value[1:].strip())
                else:
                    do_normal = True
                
                if do_normal:
                    # remove any escape characters that exist at the beginning and end of the string
                    if value.startswith("\\!"):
                        value = value[1:]
                    elif value.startswith("\\("):
                        value = value[1:]
                    elif value.startswith("\\["):
                        value = value[1:]
                    filter_dict[key] = search_schema.type_mapping(key, value.strip())
            except ValueError as e:
                raise HTTPException(422, str(e))

        if target_type in deps.PermissionCheck.type_allow_whitelist:
            # If on the whitelist, don't check permissions when searching
            roles = None
        _result, _count = crud_type.query_with_filters(
            db,
            roles,
            filter_dict,
            sort,
            skip,
            limit
        )
        return {"totalCount": _count, "resultCount": len(_result), "result": _result}


def generic_export(
    router: APIRouter,
    crud_type: CRUDBase,
    target_type: TargetTypeEnum,
    summary: str | None = None,
    description: str | None = None,
    pretty_name: str | None = None,
    admin_only: bool = False
):
    """
    Creates a POST endpoint on a router for the specified target type

    args:
    router - The router to add the route to
    crud_type - The CRUD class that handles this type of object
    target_type - The TargetTypeEnum object that refers to these objects
                    (or None if there is no TargetTypeEnum entry)
    summary (optional) - The summary to put in the documentation for this
                            endpoint
    description (optional) - The description to put in the documentation for
                            this endpoint
    pretty_name (optional) - A user-friendly name for this type of object
                            (defaults to the string of the target type)
    """
    if pretty_name is None:
        if target_type != TargetTypeEnum.none:
            pretty_name = target_type.name
        else:
            pretty_name = "<NO NAME>"
    if description is None:
        description = f"Export a {pretty_name}, and associated entries to one of the available formats"
        if pretty_name.lower()[0] in "aeiou":
            description = description.replace(" a ", " an ")
    if summary is None:
        summary = f"Export a {pretty_name}"
        if pretty_name.lower()[0] in "aeiou":
            summary = summary.replace(" a ", " an ")

    if admin_only:
        dependencies = [Depends(deps.admin_only)]
        description += " (admins only)"
    else:
        dependencies = []

    def fmt_sources_tags(obj: Any, obj_dict: dict):
        if hasattr(obj, "sources"):
            obj_dict["sources"] = ", ".join([a.name for a in obj.sources])
        if hasattr(obj, "tags"):
            obj_dict["tags"] = ", ".join([a.name for a in obj.tags])

    def fmt_promoted_to_from(obj: Any, obj_dict: dict):
        if hasattr(obj, "promoted_to_targets"):
            obj_dict["promoted to"] = ", ".join([f"{a.p1_type.value}: {a.p1_id}" for a in obj.promoted_to_targets])
            del obj_dict["promoted to targets"]
        if hasattr(obj, "promoted_from_sources"):
            obj_dict["promoted from"] = ", ".join([f"{a.p0_type.value}: {a.p0_id}" for a in obj.promoted_from_sources])
            del obj_dict["promoted from sources"]

    def fmt_table(obj: list[dict]):
        if obj != []:
            if isinstance(obj[0], dict):
                return tabulate(obj, headers="keys", tablefmt="unsafehtml")
            else:
                return ", ".join(obj)
        else:
            return ""
    
    def fmt_column_table(obj: dict):
        table = "<table>"
        for key, value in obj.items():
            table += f"<tr><td>{key}</td><td>{value}</td></tr>"
        return table + "</table>"

    def fmt_enrichments(obj: list[dict]):
        if obj != []:
            for enrichment in obj:
                tmp_data = ""
                if "data" in enrichment.keys():
                    if "markdown" in enrichment["data"].keys():
                        table = "<table><thead><tr>"
                        rows = enrichment['data']['markdown'].splitlines()
                        for column in rows[0].split("|")[1:-1]:
                            table += f"<td>{column.strip()}</td>"
                        table += "</tr><thead><tbody>"
                        for row in rows[2:]:
                            table += "<tr>"
                            for column in row.split("|")[1:-1]:
                                table += f"<td>{column.strip()}</td>"
                            table += "</tr>"
                        table += "</tbody></table>"
                        tmp_data += f"<div>{table}</div>"
                    if "plaintext" in enrichment["data"].keys():
                        tmp_data += enrichment["data"]['plaintext']
                    if "timeline" in enrichment["data"].keys():
                        tmp_data += f"<p>Timeline</p>{fmt_table(enrichment['data']['timeline'])}"
                    if "counts" in enrichment["data"].keys():
                        tmp_data += f"<p>Counts</p>{fmt_column_table(enrichment['data']['counts'])}"
                    if "unxformed" in enrichment["data"].keys():
                        enrichment["data"]["unxformed"] = fmt_column_table(enrichment["data"]["unxformed"])
                    if enrichment["enrichment class"] == "jsontree":
                        tmp_data = fmt_column_table(enrichment["data"])
                enrichment["data"] = tmp_data
            return tabulate(obj, headers="keys", tablefmt="unsafehtml")
        else:
            return ""

    def fmt_alert(alert: models.Alert):
        alert_obj = alert.as_dict(pretty_keys=True, enum_value=True)
        fmt_promoted_to_from(alert, alert_obj)
        # no need to keep the alertgroup stuff around
        del alert_obj["alertgroup"]
        # make alert data its own column in cell
        for cell in alert.data_cells:
            # skip sparkline
            if "sparkline" in cell:
                continue
            try:
                alert_obj[cell] = fmt_table(json.loads(alert.data[cell]))
            except Exception:
                alert_obj[cell] = alert.data[cell]
        return alert_obj

    def fmt_entries(db: Session, obj: Union[list[models.Entry], list[dict]], from_entry: bool = False):
        journal = ""
        if obj != []:
            for entry in obj:
                if not from_entry:
                    if isinstance(entry, dict):
                        journal += f"<h5>[{entry['id']}] {entry['owner']} @ {entry['modified']} - {entry['tlp']}</h5>"
                    else:
                        journal += f"<h5>[{entry.id}] {entry.owner} @ {entry.modified} - {entry.tlp}</h5>"
                if isinstance(entry, dict):
                    entry_data = entry.get("entry_data", {})
                else:
                    entry_data = entry.entry_data or {}

                if "html" in entry_data.keys():
                    journal += f"<div>{entry.entry_data['html']}</div>"
                if "markdown" in entry_data.keys():
                    journal = "<div><table><thead><tr>"
                    rows = entry.entry_data['markdown'].splitlines()
                    for column in rows[0].split("|")[1:-1]:
                        journal += f"<td>{column.strip()}</td>"
                    journal += "</tr><thead><tbody>"
                    for row in rows[2:]:
                        journal += "<tr>"
                        for column in row.split("|")[1:-1]:
                            journal += f"<td>{column.strip()}</td>"
                        journal += "</tr>"
                    journal += "</tbody></table></div>"

                for source in entry_data.get("promotion_sources", []):
                    if hasattr(crud, source["type"]):
                        crud_type = getattr(crud, source["type"])
                        crud_obj = crud_type.get(db, source["id"])
                        if hasattr(crud_obj, "entries"):
                            journal += f"<p>Promoted from {source['type']} {source['id']}</p>{fmt_entries(db, crud_obj.entries, True)}"
                        elif source["type"] == "alert":
                            journal += f"<p>Promoted from {source['type']} {source['id']}</p>{fmt_alert(crud_obj)}"
                if isinstance(entry, dict):
                    for child_entry in entry.get("child_entries", []):
                        journal += f"<h5>[{child_entry['id']}] {child_entry['owner']} @ {child_entry['modified']} - {child_entry['tlp']}</h5>"
                        journal += f"<div>{child_entry['entry_data']['html']}</div>"
                else:
                    for child_entry in entry.child_entries:
                        journal += f"<h5>[{child_entry.id}] {child_entry.owner} @ {child_entry.modified} - {child_entry.tlp}</h5>"
                        journal += f"<div>{child_entry.entry_data['html']}</div>"
        else:
            journal = ""
        
        return journal

    def fmt_signatures(db: Session, obj: list[models.Signature], from_guide: bool = False):
        sigs = []
        guides = ""
        for signature in obj:
            signature_obj = signature.as_dict(pretty_keys=True, enum_value=True)
            fmt_sources_tags(signature, signature_obj)
            del signature_obj["entries"]
            del signature_obj["data"]
            if not from_guide:
                for guide in signature_obj.get("associated guides", []):
                    guides += f"<p>Assoicated Guide ${guide['id']}</p>{fmt_entries(db, guide.get('entries'))}"
            del signature_obj["associated guides"]
            for cell in signature.data:
                signature_obj[cell] = signature.data[cell]
            
            sigs.append(signature_obj)
        return sigs, guides

    def remove_file(file: str) -> None:
        os.remove(file)

    @router.get(
        "/export",
        response_model=Any,
        summary=summary,
        description=description,
        dependencies=dependencies,
    )
    def export_object(
        *,
        db: Session = Depends(deps.get_db),
        audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
        id: Annotated[int, Path(...)],
        format: Annotated[ExportFormatEnum, Query(...)] = ExportFormatEnum.html,
        background_tasks: BackgroundTasks
    ) -> Any:
        # get original object
        _obj = crud_type.get(db_session=db, _id=id, audit_logger=audit_logger)
        if not _obj:
            raise HTTPException(404, f"{pretty_name} {id} not found")

        # convert it to a dict for easier conversion
        entries = {}
        _obj_dict = _obj.as_dict(pretty_keys=True, enum_value=True)
        # update the classes object to table if any
        if hasattr(_obj, "classes"):
            _obj_dict["classes"] = fmt_table(_obj_dict["classes"])

        # format tags/sources and promoted objects to tables
        fmt_sources_tags(_obj, _obj_dict)
        fmt_promoted_to_from(_obj, _obj_dict)

        # do table specific formatting
        if target_type == TargetTypeEnum.alertgroup:
            # convert the alerts to their own table
            entries["Alerts"] = []
            del _obj_dict["alerts"]
            for alert in _obj.alerts:
                entries["Alerts"].append(fmt_alert(alert))
            # format any signatures and guides
            entries["Signatures"], guides = fmt_signatures(db, _obj.associated_signatures)
            if guides != "":
                entries["Guides"] = guides
            del _obj_dict["associated signatures"]
        elif target_type == TargetTypeEnum.entity:
            # add entity appearances
            _obj_dict["enrichments"] = fmt_enrichments(_obj.enrichments)
            _obj_dict["classes"] = fmt_table(_obj.classes)
            entries["Appearances"] = []
            appearances = crud.entity.retrieve_entity_links_for_flair_pane(db, id, 0, None)
            appearances["alert_appearances"] = fmt_table(appearances["alert_appearances"])
            appearances["event_appearances"] = fmt_table(appearances["event_appearances"])
            appearances["intel_appearances"] = fmt_table(appearances["intel_appearances"])
            appearances["dispatch_appearances"] = fmt_table(appearances["dispatch_appearances"])
            appearances["product_appearances"] = fmt_table(appearances["product_appearances"])
            appearances["incident_appearances"] = fmt_table(appearances["incident_appearances"])
        elif target_type == TargetTypeEnum.guide:
            # format signatures and ignore guide
            entries["Signatures"], _ = fmt_signatures(db, crud.guide.get_signatures_for(db, id), True)
            _obj_dict["data"] = fmt_column_table(_obj_dict["data"])
        elif target_type == TargetTypeEnum.pivot:
            # make sure to get the entity types and classes
            entity_types = []
            for entity_type in _obj.entity_types:
                entity_dict = entity_type.as_dict(pretty_keys=True, enum_value=True)
                del entity_dict["entities"]
                entity_types.append(entity_dict)
            entries["Entity Types"] = fmt_table(entity_types)
            entries["Entity Classes"] = fmt_table([a.as_dict(pretty_keys=True, enum_value=True) for a in _obj.entity_classes])
        elif target_type == TargetTypeEnum.entry:
            # remove any child entries from table as it will only be in journal section
            entries["Journal"] = fmt_entries(db, [_obj], True)
            del _obj_dict["entry data"]
            del _obj_dict["child entries"]
        elif target_type == TargetTypeEnum.signature:
            # ignore the signature and get guide information
            _, guides = fmt_signatures(db, [_obj])
            _obj_dict["data"] = fmt_column_table(_obj.data)
            del _obj_dict["associated guides"]
            if guides != "":
                entries["Guides"] = guides
        elif target_type == TargetTypeEnum.incident:
            _obj_dict["data"] = fmt_column_table(_obj.data)

        # if the object has entries add them to the Journal Section
        if hasattr(_obj, "entries"):
            journal = fmt_entries(db, _obj.entries)
            if str != "":
                entries["Journal"] = journal
            del _obj_dict["entries"]

        # get any assoicated entities
        _entities, count = crud.entity.retrieve_element_entities(
            db_session=db, source_id=id, source_type=target_type
        )
        if count > 0:
            entries["Entities"] = []
            for entity in _entities:
                # maker sure everything is either a table or dict
                entity_dict = entity.as_dict(pretty_keys=True, enum_value=True)
                entity_dict["classes"] = fmt_table(entity_dict["classes"])
                entity_dict["enrichments"] = fmt_enrichments(entity_dict["enrichments"])
                entity_dict["summaries"] = fmt_table(entity_dict["summaries"])
                entity_dict["entries"] = fmt_entries(db, entity.entries)
                fmt_sources_tags(entity, entity_dict)
                entries["Entities"].append(entity_dict)

        # start creating the basic HTML document most of the css styles are to make sure things fit on a letter page format
        # can cause issues with tables as things tend to get squished
        html = ("<!DOCTYPE html><html><head><style>"
                "table {word-wrap: anywhere; -pdf-keep-in-frame-mode: shrink;}"
                "@page {size: letter portrait; @frame header_frame {-pdf-frame-content: header_content;text-align: center; font-size: 12px; margin-top: 5px;}"
                "@frame content_frame {margin: 0.5in;}}</style></head><body>")
        # create a table for the selected item data
        html += f"<h1>{pretty_name}</h1>{tabulate([_obj_dict], headers='keys', tablefmt='unsafehtml')}"
        if len(entries.keys()) != 0:
            for entry in entries:
                # for each key in the entries dict create a new section
                html += f"<h2>{entry}</h2>"
                # if the data is a list of dicts then it should be generated as a table
                if isinstance(entries[entry], list):
                    html += tabulate(entries[entry], headers="keys", tablefmt="unsafehtml")
                # if the data is a dict then make it a one row table
                elif isinstance(entries[entry], dict):
                    html += tabulate([entries[entry]], headers="keys", tablefmt="unsafehtml")
                # otherwise just print whats available, most likely this is already HTML formatted text
                else:
                    html += entries[entry]
        # end the HTML document
        html += "</body></html>"
        
        # get the site settings for creating the classification header
        settings = crud.setting.get(db, audit_logger)
        # a temporary file to hold the document to send along with the the response
        tmp_file = os.path.join(gettempdir(), f"{uuid.uuid4()}.tmp")
        with open(tmp_file, "w+b") as tmp:
            # convert the HTML to markdown
            if format == ExportFormatEnum.md:
                # insert header
                media_type = "text/markdown"
                tmp.write(f"> <center>SCOT 4.1: {settings.site_name} - {settings.environment_level}</center>\n\n{markdownify(html)}".encode())
            # save the HTML
            elif format == ExportFormatEnum.html:
                media_type = "text/html"
                # insert header
                index = html.find("<body>")
                html = html[:index] + f"<div id='header_content' style='text-align: center; font-size: 12px;'>SCOT 4.1: {settings.site_name} - {settings.environment_level}</div>" + html[index:]
                tmp.write(html.encode())
            # convert the HTML to PDF do this also for WORD DOCX as its easier to convert from PDF later
            elif format == ExportFormatEnum.pdf or format == ExportFormatEnum.docx:
                media_type = "application/pdf"
                # insert header
                index = html.find("<body>")
                html = html[:index] + f"<div id='header_content' style='text-align: center; font-size: 12px;'>SCOT 4.1: {settings.site_name} - {settings.environment_level}</div>" + html[index:]
                pisa.CreatePDF(html, dest=tmp)

        # convert from PDF to DOCX
        if format == ExportFormatEnum.docx:
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            docx_file = f"{tmp_file}.docx"
            cv = Converter(tmp_file)
            cv.convert(docx_file)
            cv.close()
            os.remove(tmp_file)
            tmp_file = docx_file
        
        # add a background task to remove the temporary file after it has been sent
        background_tasks.add_task(remove_file, tmp_file)
        return FileResponse(
            tmp_file,
            media_type=media_type,
            filename=f"{quote(target_type.value)}_{_obj.id}.{quote(format.value)}",
        )
