from typing import Any, Annotated, Dict
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum
from app.utils import create_schema_details

from .generic import (
    generic_delete,
    generic_entities,
    generic_get,
    generic_post,
    generic_put,
    generic_undelete,
    generic_history,
    generic_reflair,
    generic_search,
    generic_export,
    generic_upvote_and_downvote,
    generic_user_links
)

router = APIRouter()

# Create get, post, put, and delete endpoints
generic_export(router, crud.alert_group, TargetTypeEnum.alertgroup)
generic_get(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroupDetailed)
generic_post(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroupDetailed, schemas.AlertGroupDetailedCreate)
generic_put(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroupDetailed, schemas.AlertGroupUpdate)
generic_delete(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroupDetailed)
generic_undelete(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroupDetailed)
generic_entities(router, TargetTypeEnum.alertgroup)
generic_history(router, crud.alert_group, TargetTypeEnum.alertgroup)
generic_reflair(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroupDetailed)
generic_search(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroupSearch, schemas.AlertGroup)
generic_upvote_and_downvote(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroup)
generic_user_links(router, crud.alert_group, TargetTypeEnum.alertgroup, schemas.AlertGroupDetailed)


alertgroup_read_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.alertgroup, PermissionEnum.read))
alertgroup_modify_dep = Depends(deps.PermissionCheckId(TargetTypeEnum.alertgroup, PermissionEnum.modify))


@router.get(
    "/{id}/alerts",
    response_model=list[schemas.Alert],
    summary="Read alerts from alertgroup",
    dependencies=[alertgroup_read_dep],
)
def read_alertgroup_alerts(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Get all alerts for this alertgroup
    """
    _alert_group = crud.alert_group.get(db, id, audit_logger)
    if not _alert_group:
        raise HTTPException(404, "Alert with id %s not found" % id)
    return _alert_group.alerts


description, examples = create_schema_details(schemas.AlertAdd)


@router.post(
    "/{id}/alerts",
    response_model=schemas.Alert,
    summary="Add an alert to an alertgroup",
    dependencies=[alertgroup_read_dep],
    description=description
)
def add_alertgroup_alert(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    alert: Annotated[schemas.AlertAdd, Body(..., openapi_examples=examples)],
    _: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Add an alert to an alertgroup
    """
    try:
        alert.alertgroup_id = id
        return crud.alert.add_to_alert_group(db_session=db, obj_in=alert, audit_logger=audit_logger)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/{id}/add_column",
    response_model=schemas.AlertGroup,
    summary="Add a column to an alertgroup",
    dependencies=[alertgroup_modify_dep],
)
def add_alertgroup_column(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    column_name: str = Body(...),
    values: Dict[str, str] = Body({}),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    return crud.alert_group.add_column(db, id, column_name, values, current_user=current_user)
