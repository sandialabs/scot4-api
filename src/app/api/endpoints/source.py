from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum
from app.utils import get_search_filters

from .generic import (
    generic_delete,
    generic_get,
    generic_post,
    generic_put,
    generic_undelete,
    generic_search
)

router = APIRouter()


@router.get(
    "/target_appearance",
    response_model=schemas.ListResponse[schemas.LinkSources],
    summary="Search for objects with source"
)
def source_target_appearance(
    id: Annotated[str, Query(...)] = None,
    name: Annotated[str, Query(...)] = None,
    skip: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = 100,
    sort: Annotated[str, Query(...)] = None,
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
    _: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Return a list with all associated sources for a given source name or id
    In other words, get all of the items that have this source, and all other
    sources on that item.

    ### Search using the available fields with the optional filters:
    | | |
    | --- | --- |
    | `!` | return the opposite result |
    | `(n, n1)` | select values within the given range |
    | `!(n, n1)` | select values **NOT** within the given range |
    | `[n, n1, n2, ...]` | select multiple values within a list |
    | `![n, n1, n2, ...]` | select multiple values **NOT** within a list |
    | `{n, n1, n2, ...}` | select values that match all items in the list |
    | `\\` | use a backslash to escape a special character at the beginning of your search string; you must escape a starting parenthesis `(`, bracket `[`, or exclamation point `!` or it will be interpreted as above |

    ### Examples:
    | | |
    | --- | --- |
    | `id=!1` | return all ids that don't match the value |
    | `name=[foo, bar, baz]` | return all values that have any of the names (think OR)|
    | `name={foo, bar, baz}` | return all values that have all of the names (think AND)|

    ### Notes:
    - If none of the range or list filters work it will attempt to do a normal search
    """
    if id and name:
        raise HTTPException(422, "Submit either id or name, not both")

    and_ = False
    # check for 'and' filters
    if id is not None and id.startswith("{") and id.endswith("}"):
        id = f"[{id[1:-1]}]"
        and_ = True
    elif name is not None and name.startswith("{") and name.endswith("}"):
        name = f"[{name[1:-1]}]"
        and_ = True

    # check to make sure the source exists first
    sources, _ = crud.source.query_with_filters(db, roles, get_search_filters(schemas.SourceSearch(id=id, name=name)))
    if len(sources) == 0:
        raise HTTPException(404, "No Sources were found")

    _result, _count = crud.link.target_filter(db, [a.id for a in sources], TargetTypeEnum.source, and_, skip, limit, sort)
    return {"totalCount": _count, "resultCount": len(_result), "result": _result}


# Create get, post, put, and delete endpoints
generic_get(router, crud.source, TargetTypeEnum.source, schemas.Source)
generic_post(router, crud.source, TargetTypeEnum.source, schemas.Source, schemas.SourceCreate, permissions=False)
generic_put(router, crud.source, TargetTypeEnum.source, schemas.Source, schemas.SourceUpdate)
generic_delete(router, crud.source, TargetTypeEnum.source, schemas.Source)
generic_undelete(router, crud.source, TargetTypeEnum.source, schemas.Source)
generic_search(router, crud.source, TargetTypeEnum.source, schemas.SourceSearch, schemas.Source)


source_read_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.source, PermissionEnum.read))


@router.post("/source_by_name", response_model=schemas.Source, summary="Assign source by name")
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
    current_source = crud.source.get_by_name(db, source_name)  # Does the source exist?
    if current_source:
        if not deps.PermissionCheckId(TargetTypeEnum.source, PermissionEnum.read)(current_source.id, db, user, roles):
            raise HTTPException(403, "You do not have permission to access this resource, or it does not exist")
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, user, roles):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, create a link to the source
    return crud.source.assign_by_name(db, source_name, target_type, target_id, True, source_description, audit_logger)


@router.post("/{id}/assign", response_model=schemas.Source, dependencies=[source_read_dep], summary="Assign source by id")
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


@router.post("/{id}/remove", response_model=schemas.Source, dependencies=[source_read_dep], summary="Remove source by id")
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
    summary="Get source appearances"
)
def source_appearances(
    id: Annotated[int, Path(...)],
    skip: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = 100,
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    _: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Get appearances of this source in other objects
    """
    _appear, count = crud.appearance.query_with_filters(db, roles, {"value_type": TargetTypeEnum.source.value, "value_id": id}, None, skip, limit)
    return {"totalCount": count, "resultCount": len(_appear), "result": _appear}


@router.post("/{id}/replace/{replace_id}", response_model=schemas.Source, dependencies=[Depends(deps.admin_only)], summary="Replace a source")
def replace_source(
    id: Annotated[int, Path(...)],
    replace_id: Annotated[int, Path(...)],
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
):
    """
    Replace a source with another source for all objects, this also deletes
    the old source (admin only)
    """
    old_source = crud.source.get(db, id)
    if old_source is None:
        raise HTTPException(404, f"Source id {id} not found")

    new_source = crud.source.get(db, replace_id)
    if new_source is None:
        raise HTTPException(404, f"Source replace_id {replace_id} not found")

    # update all source links
    for link in crud.link.find_all_links(db, TargetTypeEnum.source, id):
        update = {}
        if link.v0_type == TargetTypeEnum.source and link.v0_id == id:
            update["v0_id"] = new_source.id
        elif link.v1_type == TargetTypeEnum.source and link.v1_id == id:
            update["v1_id"] = new_source.id
        crud.link.update(db, db_obj=link, obj_in=update)

    # delete old source
    crud.source.remove(db, id)
    # return new source
    return new_source
