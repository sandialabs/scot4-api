from typing import Annotated
from fastapi import APIRouter, Body, Path
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Body

from app import crud, schemas, models
from app.api import deps
from app.utils import create_schema_details

router = APIRouter()


@router.get("/{id}", response_model=schemas.Popularity, summary="Get popularity", description="Get a popularity object")
def read_object(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.Popularity:
    _obj = crud.popularity.get(db, id)
    if not _obj:
        raise HTTPException(404, f"Popularity {id} not found")

    if not crud.user.is_superuser(current_user) and _obj.owner_id != current_user.id:
        raise HTTPException(404, "Popularity not found")

    return _obj


description, examples = create_schema_details(schemas.PopularityCreate, "Create a new popularity associated with a target type")


@router.post("/", response_model=schemas.Popularity, summary="Create a new popularity metric", description=description)
def create_object(
    *,
    db: Session = Depends(deps.get_db),
    popularity: Annotated[schemas.PopularityCreate, Body(..., openapi_examples=examples, alias="popularity")],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.Popularity:
    # can only create your own stuff
    popularity.owner_id = current_user.id
    # check if user has already voted for target
    _obj = crud.popularity.get_user_metric(db, popularity.target_type, popularity.target_id, popularity.owner_id)
    # if exits raise error
    if _obj is not None:
        raise HTTPException(422, "User has already voted")

    return crud.popularity.create(db, obj_in=popularity)


description, examples = create_schema_details(schemas.PopularityUpdate, "Update one or more fields of a Popularity")


@router.put("/{id}", response_model=schemas.Popularity, summary="Update popularity", description=description)
def update_object(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    obj: Annotated[schemas.PopularityUpdate, Body(..., openapi_examples=examples, alias="popularity")],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> schemas.Popularity:
    _obj = crud.popularity.get(db, id)
    if not _obj:
        raise HTTPException(404, "Popularity not found")

    if _obj.owner_id != current_user.id:
        raise HTTPException(404, "Popularity not found")

    return crud.popularity.update(db, db_obj=_obj, obj_in=obj)


@router.delete("/{id}", response_model=schemas.Popularity, summary="Delete a popularity", description=description)
def delete_object(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> schemas.Popularity:
    _obj_group = crud.popularity.get(db, id)

    if not _obj_group:
        raise HTTPException(404, "Popularity not found")

    if _obj_group.owner_id != current_user.id:
        raise HTTPException(404, "Popularity not found")

    return crud.popularity.remove(db, _id=id)
