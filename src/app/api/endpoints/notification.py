from typing import Any, Annotated
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Body, Query, HTTPException, Response
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import UserLinkEnum

router = APIRouter()


# Reads unacknowledged notification data
# For a specific user
@router.get("/", response_model=schemas.ListResponse[schemas.Notification])
def read_notifications(
    *,
    db: Session = Depends(deps.get_db),
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = 100,
    include_acked: Annotated[bool, Query(...)] = False,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get ALL notification data for the current user.
    """
    _notifications, count = crud.notification.get_notifications_for_user(
        db_session=db, user_id=current_user.id, limit=limit,
        skip=skip, include_acked=include_acked
    )
    return {"totalCount": count, "resultCount": len(_notifications), "result": _notifications}


@router.post("/ack")  # response_model=schemas.ListResponse[schemas.NotificationUpdate]
def ack_notifications(
    *,
    db: Session = Depends(deps.get_db),
    ack: Annotated[schemas.NotificationAck, Body(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger)
) -> list[int]:
    """
    Acknowledges notifications by ID
    """
    try:
        return crud.notification.ack_notifications(
            db, ack.notification_ids, current_user.id, audit_logger
        )
    except Exception as e:
        raise HTTPException(422, "Error: " + str(e))


@router.post(
    "/broadcast", status_code=201, dependencies=[Depends(deps.admin_only)]
)
def broadcast_notification(
    *,
    db: Session = Depends(deps.get_db),
    broadcast: Annotated[schemas.NotificationBroadcast, Body(...)],
    current_user: models.User = Depends(deps.get_current_active_user)
) -> None:
    """
    Sends a notification to every user (default priority medium and expiry 12 hours)
    """
    if "expires" not in broadcast.model_fields_set:
        broadcast.expires = datetime.now(timezone.utc) + timedelta(hours=12)
    try:
        crud.notification.broadcast_notification(
            db, broadcast.message, broadcast.priority, broadcast.expires
        )
    except Exception as e:
        raise HTTPException(422, "Error: " + e)


@router.post("/subscribe", response_model=schemas.UserLinks)
def subscribe(
    *,
    db: Session = Depends(deps.get_db),
    subscribe: Annotated[schemas.NotificationSubscribe, Body(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger)
) -> Any:
    """
    Subscribes to notifications for a particular object
    """
    link = crud.user_links.find_link(
        db, subscribe.target_type, subscribe.target_id,
        current_user.id, UserLinkEnum.subscription
    )
    if link:
        raise HTTPException(422,
            f"You are already subscribed to {subscribe.target_type} {subscribe.target_id}")
    try:
        sub_create = schemas.UserLinksCreate(
            link_type=UserLinkEnum.subscription,
            target_type=subscribe.target_type,
            target_id=subscribe.target_id,
            owner_id=current_user.id
        )
        return crud.user_links.create(db, obj_in=sub_create, audit_logger=audit_logger)
    except Exception as e:
        raise HTTPException(422, "Error: " + str(e))


@router.post("/unsubscribe", response_model=schemas.UserLinks)
def unsubscribe(
    *,
    db: Session = Depends(deps.get_db),
    subscribe: Annotated[schemas.NotificationSubscribe, Body(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger)
) -> Any:
    """
    Unsubscribes from notifications to a particular object
    """
    link = crud.user_links.find_link(
        db, subscribe.target_type, subscribe.target_id,
        current_user.id, UserLinkEnum.subscription
    )
    if not link:
        raise HTTPException(422,
            f"You are not subscribed to {subscribe.target_type} {subscribe.target_id}")
    try:
        return crud.user_links.remove(db, _id=link.id, audit_logger=audit_logger)
    except Exception as e:
        raise HTTPException(422, "Error: " + str(e))
