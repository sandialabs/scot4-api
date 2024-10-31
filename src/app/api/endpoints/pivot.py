from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.enums import TargetTypeEnum
from app.utils import create_schema_details

from .generic import generic_delete, generic_get, generic_post, generic_put, \
    generic_history, generic_search, generic_export

router = APIRouter()
description, examples = create_schema_details(schemas.pivot.PivotAddEntityClasses)
description_types, examples_types = create_schema_details(schemas.pivot.PivotAddEntityTypes)


# Create get, post, put, and delete endpoints
generic_export(router, crud.pivot, TargetTypeEnum.pivot)
generic_get(router, crud.pivot, TargetTypeEnum.pivot, schemas.Pivot)
generic_delete(router, crud.pivot, TargetTypeEnum.pivot, schemas.Pivot)
generic_history(router, crud.pivot, TargetTypeEnum.pivot)
generic_post(router, crud.pivot, TargetTypeEnum.pivot, schemas.Pivot, schemas.PivotCreate)
generic_put(router, crud.pivot, TargetTypeEnum.pivot, schemas.Pivot, schemas.PivotUpdate)
generic_search(router, crud.pivot, TargetTypeEnum.pivot, schemas.PivotSearch, schemas.Pivot)


@router.put(
    "/{id}/entity_class",
    response_model=schemas.Pivot,
    summary="Add Entity Class",
    description=f"Add Entity Types\n{description}",
    # dependencies=[Depends(deps.admin_only)]  # all users can update pivots for now
)
def add_entity_classes(
    *,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    id: Annotated[int, Path(...)],
    request: Annotated[schemas.pivot.PivotAddEntityClasses, Body(..., openapi_examples=examples)]
) -> Any:
    _obj = crud.pivot.get(db_session=db, _id=id)
    if not _obj:
        raise HTTPException(404, f"Pivot {id} not found")
    try:
        _pivot = crud.pivot.add_entity_classes(db_session=db, db_obj=_obj, entity_classes=request.entity_classes, audit_logger=audit_logger)
    except Exception as e:
        raise HTTPException(400, str(e))
    return _pivot


@router.put(
    "/{id}/entity_type",
    response_model=schemas.Pivot,
    summary="Add Entity Types to pivot",
    description=f"Add Entity Types to Pivot\n{description}",
    # dependencies=[Depends(deps.admin_only)]  # all users can update pivots for now
)
def add_entity_types(
    *,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    id: Annotated[int, Path(...)],
    request: Annotated[schemas.pivot.PivotAddEntityTypes, Body(..., openapi_examples=examples_types)],
) -> Any:
    _obj = crud.pivot.get(db_session=db, _id=id)
    if not _obj:
        raise HTTPException(404, detail=f"Pivot {id} not found")
    try:
        _pivot = crud.pivot.add_entity_types(db_session=db, db_obj=_obj, entity_types=request.entity_types, audit_logger=audit_logger)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _pivot
