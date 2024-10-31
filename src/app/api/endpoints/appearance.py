from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.utils import create_schema_details

from .generic import generic_search

router = APIRouter()
description, examples = create_schema_details(schemas.AppearanceCreate)
description_update, examples_update = create_schema_details(schemas.AppearanceUpdate)


generic_search(router, crud.appearance, None, schemas.AppearanceSearch, schemas.Appearance, summary="Search appearances", pretty_name="Appearances")


# Appearances can only be created (directly) by admins
@router.post(
    "/", response_model=schemas.Appearance, dependencies=[Depends(deps.admin_only)], description=description
)
def create_appearance(
    *,
    db: Session = Depends(deps.get_db),
    appearance: Annotated[schemas.AppearanceCreate, Body(..., openapi_examples=examples)],
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger)
) -> Any:
    """
    Create new appearance
    """
    return crud.appearance.create(db_session=db, obj_in=appearance, audit_logger=audit_logger)


@router.get("/{id}", response_model=schemas.Appearance)
def read_appearance(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger)
) -> Any:
    """
    Get appearance by ID.
    """
    _appearance = crud.appearance.get(db_session=db, _id=id, audit_logger=audit_logger)
    if not _appearance:
        raise HTTPException(404, "Appearance not found")

    return _appearance


@router.put(
    "/{id}", response_model=schemas.Appearance, dependencies=[Depends(deps.admin_only)], description=description_update
)
def update_appearance(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    appearance: Annotated[schemas.AppearanceUpdate, Body(..., openapi_examples=examples_update)],
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger)
) -> Any:
    """
    Update an appearance
    """
    _appearance = crud.appearance.get(db_session=db, _id=id)
    if not _appearance:
        raise HTTPException(404, "Appearance not found")
    updated = crud.appearance.update(
        db_session=db, db_obj=_appearance, obj_in=appearance, audit_logger=audit_logger
    )
    return updated


@router.delete(
    "/{id}", response_model=schemas.Appearance, dependencies=[Depends(deps.admin_only)]
)
def delete_appearance(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger)
) -> Any:
    """
    Delete an appearance
    """
    _appearance = crud.appearance.get(db_session=db, _id=id)
    if not _appearance:
        raise HTTPException(404, "Appearance not found")
    return crud.appearance.remove(db_session=db, _id=id, audit_logger=audit_logger)
