from typing import Annotated
from fastapi import APIRouter, Body, Path, Query
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Body

from app import crud, schemas, models
from app.api import deps
from app.utils import create_schema_details
from app.enums import UserLinkEnum

router = APIRouter()


@router.get("/", response_model=schemas.ListResponse[schemas.UserLinks], summary="Search for a user link", description="Search for a user link object")
def read_object(
    *,
    db: Session = Depends(deps.get_db),
    link_type: Annotated[UserLinkEnum, Query(...)],
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = 100,
    sort: Annotated[str | None, Query(...)] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.ListResponse[schemas.UserLinks]:
    _result, _count = crud.user_links.query_with_filters(db, None, {"link_type": link_type, "owner_id": current_user.id}, sort, skip, limit)
    return {"totalCount": _count, "resultCount": len(_result), "result": _result}


@router.get("/{id}", response_model=schemas.UserLinks, summary="Get a user link", description="Get a user link object")
def read_object(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.UserLinks:
    _obj = crud.user_links.get(db, id)
    if not _obj:
        raise HTTPException(404, f"User Link {id} not found")

    if not crud.user.is_superuser(current_user) and _obj.owner_id != current_user.id:
        raise HTTPException(404, "User Link not found")

    return _obj


description, examples = create_schema_details(schemas.UserLinksCreate, "Create a new user link associated with a target type")


@router.post("/", response_model=schemas.UserLinks, summary="Create a new User Link", description=description)
def create_object(
    *,
    db: Session = Depends(deps.get_db),
    user_link: Annotated[schemas.UserLinksCreate, Body(..., openapi_examples=examples, alias="user_link")],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.UserLinks:
    # can only create your own stuff
    user_link.owner_id = current_user.id
    return crud.user_links.create(db, obj_in=user_link)


description, examples = create_schema_details(schemas.UserLinksUpdate, "Update one or more fields of a User Link")


@router.put("/{id}", response_model=schemas.UserLinks, summary="Update a user link", description=description)
def update_object(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    obj: Annotated[schemas.UserLinksUpdate, Body(..., openapi_examples=examples, alias="user_link")],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> schemas.UserLinks:
    _obj = crud.user_links.get(db, id)
    if not _obj:
        raise HTTPException(404, "User Link not found")

    if _obj.owner_id != current_user.id:
        raise HTTPException(404, "User Link not found")

    return crud.user_links.update(db, db_obj=_obj, obj_in=obj)


@router.delete("/{id}", response_model=schemas.UserLinks, summary="Delete a user link", description=description)
def delete_object(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> schemas.UserLinks:
    _obj_group = crud.user_links.get(db, id)

    if not _obj_group:
        raise HTTPException(404, "User Link not found")
    
    if _obj_group.owner_id != current_user.id:
        raise HTTPException(404, "User Link not found")

    return crud.user_links.remove(db, _id=id)
