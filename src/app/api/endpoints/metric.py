from typing import Any, Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, Body, Path
from sqlalchemy.orm import Session
from pydantic.json_schema import SkipJsonSchema

from app import crud, models, schemas
from app.api import deps
from app.utils import create_schema_details

router = APIRouter()


# Reads ALL metrics data
# Open to all users
@router.get("/", summary="Get metrics", response_model=list[schemas.Metric])
def read_metrics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get ALL metrics data (no pagination)
    """
    return crud.metric.get_multi(db)


# Creates a new metric
# Admin only
_, examples = create_schema_details(schemas.MetricCreate)


@router.post("/", response_model=schemas.Metric, summary="Create a metric")
def create_metric(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    metric: Annotated[schemas.MetricCreate, Body(..., openapi_examples=examples)],
) -> Any:
    """
    Creates a metric category. `name` is the category's short name
    (e.g. "Alerts Closed"), `tooltip` is a description of the category (e.g.
    "Alerts closed in last day"), and `parameters` is a dictionary describing the
    conditions being tracked. The available parameters are:
     * "what" - the action being taken, in the set ["create", "read",
                 "update", "delete", "undelete", "login"]
     * "type" - the type of thing being acted upon
     * "id" - the id of the thing being acted upon
     * "data" - a dictionary whose data must match the data in the event

    For example, a parameters dictionary of
        `{"what": "update", "type": "alert", "data": {"status": "closed"}}`
    would count the number of alert closing events.
    """
    return crud.metric.create(db, obj_in=metric, audit_logger=audit_logger)


@router.get("/results", response_model=list[schemas.MetricResult], summary="Get metric results")
def get_results(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    metric_ids: Annotated[list[int] | SkipJsonSchema[None], Query()] = None,
    dates: Annotated[list[datetime] | SkipJsonSchema[None], Query(..., min_items=1, max_items=2)] = None,
    exclude_users: Annotated[list[str] | SkipJsonSchema[None], Query()] = None,
) -> Any:
    """
    Get results from all metrics
    """
    return crud.metric.get_results_for_metrics(db, metric_ids, dates, exclude_users)


# Gets single gamification data
# Open to all users
@router.get("/{id}", response_model=schemas.Metric, summary="Get a metric")
def read_metric(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    id: Annotated[int, Path(...)]
) -> Any:
    """
    Get the data of a metric
    """
    _metric = crud.metric.get(db, id)
    if _metric:
        return _metric
    else:
        raise HTTPException(404, f"metric {id} not found")
