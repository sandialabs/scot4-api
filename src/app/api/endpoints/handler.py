from datetime import datetime
from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import TargetTypeEnum

from .generic import generic_delete, generic_get, generic_post, generic_put

router = APIRouter()

# Create get, post, put, and delete endpoints
generic_get(router, crud.handler, TargetTypeEnum.none, schemas.Handler, pretty_name="handler")
generic_post(
    router,
    crud.handler,
    TargetTypeEnum.none,
    schemas.Handler,
    schemas.HandlerCreate,
    pretty_name="handler",
)
generic_put(
    router,
    crud.handler,
    TargetTypeEnum.none,
    schemas.Handler,
    schemas.HandlerUpdate,
    pretty_name="handler",
)
generic_delete(router, crud.handler, TargetTypeEnum.none, schemas.Handler, pretty_name="handler")


@router.get(
    "/",
    response_model=schemas.ListResponse[schemas.Handler],
    summary="Get handlers in date range",
)
def handler_date_range(
    user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
    skip: Annotated[int, Path(...)] = 0,
    limit: Annotated[int, Query(...)] = 100,
    start_date: Annotated[datetime, Query(...)] = datetime.min,
    end_date: Annotated[datetime, Query(...)] = datetime.max,
) -> Any:
    """
    List all handler assignments that fall at least partially in the given
    date range
    """
    if end_date < start_date:
        raise HTTPException(422, "start_date must be before end_date")
    _handlers, count = crud.handler.get_handlers_in_date_range(
        db_session=db, start_date=start_date, end_date=end_date, skip=skip, limit=limit
    )
    return {"totalCount": count, "resultCount": len(_handlers), "result": _handlers}
