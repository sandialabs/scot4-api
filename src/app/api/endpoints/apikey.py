import uuid
from typing import Any, Union, Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", summary="Read api keys", response_model=schemas.ListResponse[schemas.ApiKey])
def read_apikeys(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = 100,
) -> Any:
    """
    Retrieve all api keys owned by this user (paginated)
    """
    apikeys, count = crud.apikey.query_with_filters(db, None, {"owner": current_user.username}, None, skip, limit)
    return {"totalCount": count, "resultCount": len(apikeys), "result": apikeys}


@router.post("/", summary="Create an api key", response_model=schemas.ApiKey)
def create_apikey(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    roles: Annotated[list[Union[str, int]], Body(..., examples=[["rolename", 1]])] = []
) -> Any:
    """
    Create a new api key; specific roles can be assigned to this new key by
    including an array of role names or ids in the request body
    """
    # Translate role ids/names into the actual role objects
    resolved_roles = []
    for r in roles:
        role = None
        if isinstance(r, int):
            role = crud.role.get(db, r)
        elif isinstance(r, str):
            role = crud.role.get_role_by_name(db, r)
        if role is None:
            raise HTTPException(422, f"Role {r} not found")
        if role not in current_roles and not crud.user.is_superuser(current_user):
            raise HTTPException(422, f"You do not have permission to assign role {role.name} to an api key")
        resolved_roles.append(role)

    apikey = crud.apikey.create(db, obj_in=schemas.ApiKey(key=str(uuid.uuid4()).upper(), owner=current_user.username))
    for role in resolved_roles:
        apikey.roles.append(role)
    db.add(apikey)
    return apikey


@router.put("/{key}", summary="Update an api key", response_model=schemas.ApiKey)
def update_apikey(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    key: Annotated[str, Path(...)],
    active: Annotated[bool | None, Body(...)] = None,
    roles: Annotated[list[Union[int, str]] | None, Body()] = None,
) -> Any:
    """
    Update an api key, changing its roles and/or active status
    """
    # Search for the api key
    apikey = crud.apikey.get(db_session=db, key=key)
    if not apikey or (apikey.owner != current_user.username and not crud.user.is_superuser(current_user)):
        raise HTTPException(404, "Item not found")
    # Do the actual update
    update_dict = {}
    if active is not None:
        update_dict["active"] = active
    if roles is not None:
        # Translate role ids/names into the actual role objects
        resolved_roles = []
        for r in roles:
            role = None
            if isinstance(r, int):
                role = crud.role.get(db, r)
            elif isinstance(r, str):
                role = crud.role.get_role_by_name(db, r)
            if role is None:
                raise HTTPException(422, f"Role {r} not found")
            if role not in current_roles and not crud.user.is_superuser(current_user):
                raise HTTPException(422, f"You do not have permission to assign role {role.name} to an api key")
            resolved_roles.append(role)
        update_dict["roles"] = resolved_roles
    updated = crud.apikey.update(db, db_obj=apikey, obj_in=update_dict)
    return updated


@router.get("/{key}", summary="Get an api key", response_model=schemas.ApiKey)
def read_apikey(
    *,
    db: Session = Depends(deps.get_db),
    key: Annotated[str, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get details of an api key
    """
    apikey = crud.apikey.get(db, key)
    if not apikey:
        raise HTTPException(404, "Api key not found")
    if not crud.user.is_superuser(current_user) and (apikey.owner != current_user.username):
        raise HTTPException(404, "Api key not found")
    return apikey


@router.delete("/{key}", summary="Delete an api key", response_model=schemas.ApiKey)
def delete_apikey(
    *,
    db: Session = Depends(deps.get_db),
    key: Annotated[str, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete an api key
    """
    apikey = crud.apikey.get(db, key)
    if not apikey:
        raise HTTPException(404, "Api key not found")
    if not crud.user.is_superuser(current_user) and (
        apikey.owner != current_user.username
    ):
        raise HTTPException(404, "Api key not found")
    apikey = crud.apikey.remove(db, key=key)
    return apikey
