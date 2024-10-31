from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app import crud, models, schemas
from app.api import deps
from app.enums import TargetTypeEnum, PermissionEnum
from app.utils import create_schema_details

from .generic import (
    generic_delete,
    generic_entities,
    generic_entries,
    generic_get,
    generic_post,
    generic_undelete,
    generic_history,
    generic_search
)

router = APIRouter()
description, examples = create_schema_details(schemas.AlertUpdate)

# Create get, post, put, and delete endpoints
generic_get(router, crud.alert, TargetTypeEnum.alert, schemas.Alert)
generic_post(
    router, crud.alert, TargetTypeEnum.alert, schemas.Alert, schemas.AlertCreate
)
generic_delete(router, crud.alert, TargetTypeEnum.alert, schemas.Alert)
generic_undelete(router, crud.alert, TargetTypeEnum.alert, schemas.Alert)
generic_entries(router, TargetTypeEnum.alert)
generic_entities(router, TargetTypeEnum.alert)
generic_search(router, crud.alert, TargetTypeEnum.alert, schemas.AlertSearch, schemas.Alert)
generic_history(router, crud.alert, TargetTypeEnum.alert)


# Custom PUT so that you can modify alerts if you have access to the alertgroup
@router.put(
    "/{id}",
    response_model=schemas.Alert,
    summary="Update an alert",
    description=description
)
def update_alert(
    *,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    id: Annotated[int, Path(...)],
    obj: Annotated[schemas.AlertUpdate, Body(..., openapi_examples=examples)],
) -> Any:
    _obj = crud.alert.get(db_session=db, _id=id)
    if not _obj:
        raise HTTPException(404, f"Alert {id} not found")
    try:
        # Raises HTTPException on no permissions
        deps.PermissionCheckId(TargetTypeEnum.alert, PermissionEnum.modify)(
            id, db, current_user, current_roles
        )
    except HTTPException:
        # Raises HTTPException on no permissions
        deps.PermissionCheckId(TargetTypeEnum.alertgroup, PermissionEnum.modify)(
            _obj.alertgroup_id, db, current_user, current_roles
        )
    # Perform validation on the state of the new object
    try:
        schemas.Alert.model_validate(_obj)
    except ValidationError as e:
        raise HTTPException(422, f"Validation error: {e}")

    try:
        updated = crud.alert.update(
            db_session=db, db_obj=_obj, obj_in=obj, audit_logger=audit_logger
        )
    except ValueError as e:
        raise HTTPException(422, f"Error when updating alert: {e}")

    return updated
