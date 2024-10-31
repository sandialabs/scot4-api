import uuid
from typing import Any, Union, Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=schemas.ListResponse[schemas.ApiKey])
def read_apikeys(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = 100,
) -> Any:
    """
    Retrieve all api keys owned by this user (paginated)
    """
    filter_dict = {"owner": current_user.username}
    apikeys, count = crud.apikey.query_with_filters(
        db_session=db, filter_dict=filter_dict, skip=skip, limit=limit
    )
    return {"totalCount": count, "resultCount": len(apikeys), "result": apikeys}


@router.post("/", response_model=schemas.ApiKey)
def create_apikey(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    roles: list[Union[str, int]] | None = []
) -> Any:
    """
    Create a new api key; specific roles can be assigned to this new key by
    including an array of role names or ids
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

    new_key = schemas.ApiKey(key=str(uuid.uuid4()).upper(), owner=current_user.username)
    apikey = crud.apikey.create(db_session=db, obj_in=new_key)
    for role in resolved_roles:
        apikey.roles.append(role)
    db.add(apikey)
    return apikey


@router.put("/{key}", response_model=schemas.ApiKey)
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
    Update an api key (only roles and active allowed)
    """
    # Search for the api key
    apikey = crud.apikey.get(db_session=db, key=key)
    if not apikey or (
        apikey.owner != current_user.username
        and not crud.user.is_superuser(current_user)
    ):
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
    updated = crud.apikey.update(db_session=db, db_obj=apikey, obj_in=update_dict)
    return updated


@router.get("/{key}", response_model=schemas.ApiKey)
def read_apikey(
    *,
    db: Session = Depends(deps.get_db),
    key: Annotated[str, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get api key by ID.
    """
    apikey = crud.apikey.get(db_session=db, key=key)
    if not apikey:
        raise HTTPException(404, "Api key not found")
    if not crud.user.is_superuser(current_user) and (apikey.owner != current_user.username):
        raise HTTPException(404, "Api key not found")
    return apikey


@router.delete("/{key}", response_model=schemas.ApiKey)
def delete_apikey(
    *,
    db: Session = Depends(deps.get_db),
    key: Annotated[str, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete an api key
    """
    apikey = crud.apikey.get(db_session=db, key=key)
    if not apikey:
        raise HTTPException(404, "Api key not found")
    if not crud.user.is_superuser(current_user) and (
        apikey.owner != current_user.username
    ):
        raise HTTPException(404, "Api key not found")
    apikey = crud.apikey.remove(db_session=db, key=key)
    return apikey
