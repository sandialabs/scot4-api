import json
import asyncio
import signal
from typing import Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app import models
from app.api import deps
from app.models.audit import Audit
from app.models.notification import Notification

router = APIRouter()

# Close all connections on SIGINT, SIGTERM (more graceful shutdown)
shutdown = False


def signal_shutdown(*args):
    global shutdown
    shutdown = True


@router.get('/')
async def stream_audits(
    *,
    request: Request,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Search all audits based on the given parameters
    """
    if signal.getsignal(signal.SIGINT) != signal_shutdown:
        signal.signal(signal.SIGINT, signal_shutdown)
        signal.signal(signal.SIGTERM, signal_shutdown)

    async def event_generator():
        audit_checkpoint = None
        notification_checkpoint = None
        while audit_checkpoint is None:
            audit_checkpoint = db.query(Audit.id).order_by(Audit.id.desc()).first()
            if audit_checkpoint is None:
                await asyncio.sleep(10)
            else:
                audit_checkpoint = audit_checkpoint[0]
                notification_checkpoint = db.query(Notification.id).order_by(Notification.id.desc()).first()
                if notification_checkpoint is not None:
                    notification_checkpoint = notification_checkpoint[0]
                else:
                    notification_checkpoint = 0
        while not shutdown:
            if await request.is_disconnected():
                break
            # Check for any new audit logs
            _audits = db.query(Audit.id, Audit.when_date, Audit.what, Audit.thing_type, Audit.thing_id, Audit.username, Audit.audit_data).filter(Audit.id > audit_checkpoint).order_by(Audit.id.desc()).all()
            db.commit()
            if len(_audits) > 0:
                audit_checkpoint = _audits[0][0]
            for record in _audits:
                if record[6] is not None and record[3] == 'link':
                    yield json.dumps({
                        'what': record[2],
                        'when': record[1].strftime('%Y-%m-%d %H:%M:%s'),
                        'element_type': record[3],
                        'element_id': record[4],
                        'username': record[5],
                        'v0_id': record[6].get("v0_id"),
                        'v0_type': record[6].get("v0_type"),
                        'v1_id': record[6].get("v1_id"),
                        'v1_type': record[6].get("v1_type")
                    })
                elif record[3] == 'entry' and record[6] is not None:
                    # We need to get the entry target id and target type.
                    yield json.dumps({'what': record[2], 'when': record[1].strftime('%Y-%m-%d %H:%M:%s'), 'element_type': record[3], 'element_id': record[4], 'username': record[5], 'target_id': record[6].get("target_id"), 'target_type': record[6].get("target_type")})
                elif record[3] == 'notification':
                    # Only notify on modification to own notification (for multi-window users)
                    if record[5] == current_user.username:
                        yield json.dumps({'what': record[2], 'when': record[1].strftime('%Y-%m-%d %H:%M:%s'), 'element_type': record[3], 'element_id': record[4], 'username': record[5], 'data': record[6]})
                else:
                    yield json.dumps({'what': record[2], 'when': record[1].strftime('%Y-%m-%d %H:%M:%s'), 'element_type': record[3], 'element_id': record[4], 'username': record[5]})
            # Check for new notifications
            notifications = db.query(Notification.id, Notification.created).filter(Notification.id > notification_checkpoint).filter(Notification.user_id == current_user.id).order_by(Notification.id.desc()).all()
            if len(notifications) > 0:
                notification_checkpoint = notifications[0][0]
            for record in notifications:
                yield json.dumps({'what': 'create', 'when': record[1].strftime('%Y-%m-%d %H:%M:%s'), 'element_type': 'notification', 'element_id': record[0], 'username': current_user.username})
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
