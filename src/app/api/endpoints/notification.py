from typing import Any, Annotated
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


# Reads unacknowledged notification data
# For a specific user
@router.get("/", response_model=schemas.ListResponse[schemas.Notification])
def read_notifications(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get ALL notification data for the current user.
    """
    _notifications, count = crud.notification.query_with_filters(db_session=db, filter_dict={'user_id': current_user.id, 'ack': False})
    return {"totalCount": count, "resultCount": len(_notifications), "result": _notifications}


@router.post("/ack/")  # response_model=schemas.ListResponse[schemas.NotificationUpdate]
def ack_notifications(
    *,
    db: Session = Depends(deps.get_db),
    body: Annotated[dict[str, list[int]], Body(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Acknowledges notifications by ID
    """
    _notifications = []
    notification_ids = body['notification_ids']
    for notification_id in notification_ids:
        notification_db = crud.notification.get(db_session=db, _id=notification_id)
        obj_in = schemas.notification.NotificationUpdate(ack=True)
        updated = crud.notification.update(db_session=db, db_obj=notification_db, obj_in=obj_in)
        notification_db = crud.notification.get(db_session=db, _id=notification_id)
    return True
