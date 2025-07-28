from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path
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
tag_read_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.tag, PermissionEnum.read))


@router.get(
    "/target_appearance",
    response_model=schemas.ListResponse[schemas.LinkTags],
    summary="Search for objects with tag"
)
def tag_target_appearance(
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
    Return a list with all associated tags for a given tag name or id
    In other words, get all of the items that have this tag, and all other
    tags on that item.

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
    - When searching by name, a wildcard search will be performed for anything that includes the name i.e. searching "foo" will return foo and bar-foo-bar
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

    # get a list of tag ids from a list of names
    tags, _ = crud.tag.query_with_filters(db, roles, get_search_filters(schemas.TagSearch(id=id, name=name)))
    if len(tags) == 0:
        raise HTTPException(404, "No Tags were found")

    _result, _count = crud.link.target_filter(db, [a.id for a in tags], TargetTypeEnum.tag, and_, skip, limit, sort)
    return {"totalCount": _count, "resultCount": len(_result), "result": _result}


# Create get, post, put, and delete endpoints
generic_get(router, crud.tag, TargetTypeEnum.tag, schemas.Tag)
generic_post(router, crud.tag, TargetTypeEnum.tag, schemas.Tag, schemas.TagCreate, permissions=False)
generic_put(router, crud.tag, TargetTypeEnum.tag, schemas.Tag, schemas.TagUpdate)
generic_delete(router, crud.tag, TargetTypeEnum.tag, schemas.Tag)
generic_undelete(router, crud.tag, TargetTypeEnum.tag, schemas.Tag)
generic_search(router, crud.tag, TargetTypeEnum.tag, schemas.TagSearch, schemas.Tag)


@router.post("/{id}/tag", response_model=schemas.Tag, dependencies=[tag_read_dep], summary="Assign tag by id")
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
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, user, roles):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, create a link to the tag
    tag = crud.tag.assign(db, id, target_type, target_id, audit_logger)
    if not tag:
        raise HTTPException(404, f"Tag {id} not found")

    return tag


@router.post("/tag_by_name", response_model=schemas.Tag, summary="Assign tag by name")
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
        if not deps.PermissionCheckId(TargetTypeEnum.tag, PermissionEnum.read)(current_tag.id, db, user, roles):
            raise HTTPException(403, "You do not have permission to access this resource, or it does not exist")
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, user, roles):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, create a link to the tag
    return crud.tag.assign_by_name(db, tag_name, target_type, target_id, True, tag_description, audit_logger)


@router.post("/{id}/untag", response_model=schemas.Tag, dependencies=[tag_read_dep], summary="Remove tag by id")
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
    Remove a tag from an object; you can only remove a tag from an object if
    you have read permissions on the tag and modify permissions on the object.
    """
    # Get effective permissions on target object
    if not deps.PermissionCheckId(target_type, PermissionEnum.modify)(target_id, db, user, roles):
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} does not exist, or you do not have modify permissions on it")
    # If the user has permission, delete all links to the tag
    tag = crud.tag.unassign(db, id, target_type, target_id, audit_logger)
    if tag:
        return tag
    else:
        raise HTTPException(404, f"{target_type.name.capitalize()} with id {target_id} is not tagged with tag {id}")


@router.get(
    "/{id}/appearance",
    response_model=schemas.ListResponse[schemas.Appearance],
    dependencies=[tag_read_dep],
    summary="Get tag appearances"
)
def tag_appearances(
    id: Annotated[int, Path(...)],
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = 100,
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    _: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Get appearances of this tag in other objects
    """
    _appear, count = crud.appearance.query_with_filters(db, roles, {"value_type": TargetTypeEnum.tag.value, "value_id": id}, None, skip, limit)
    return {"totalCount": count, "resultCount": len(_appear), "result": _appear}


@router.post("/{id}/replace/{replace_id}", response_model=schemas.Tag, dependencies=[Depends(deps.admin_only)])
def tag_replace(
    id: Annotated[int, Path(...)],
    replace_id: Annotated[int, Path(...)],
    user: models.User = Depends(deps.get_current_active_user),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
):
    """
    Replace a tag with another tag for all objects, this also deletes
    the old tag (admin only)
    """
    # permission check on the replace id?
    deps.PermissionCheckId(TargetTypeEnum.source, PermissionEnum.read)(replace_id, db, user, roles)

    old_tag = crud.tag.get(db, id)
    if old_tag is None:
        raise HTTPException(404, f"Tag id {id} not found")

    new_tag = crud.tag.get(db, replace_id)
    if new_tag is None:
        raise HTTPException(404, f"Tag replace_id {replace_id} not found")

    # update all tag links
    for link in crud.link.find_all_links(db, TargetTypeEnum.tag, old_tag.id):
        update = {}
        if link.v0_type == TargetTypeEnum.tag and link.v0_id == old_tag.id:
            update["v0_id"] = new_tag.id
        elif link.v1_type == TargetTypeEnum.tag and link.v1_id == old_tag.id:
            update["v1_id"] = new_tag.id
        link = crud.link.update(db, db_obj=link, obj_in=update)

    # delete old tag
    crud.tag.remove(db, id)
    # return new tag
    return new_tag
