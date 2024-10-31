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
        checkpoint = None
        while checkpoint is None:
            checkpoint = db.query(Audit.id).order_by(Audit.id.desc()).first()
            if checkpoint is None:
                await asyncio.sleep(10)
            else:
                checkpoint = checkpoint[0]
        while not shutdown:
            if await request.is_disconnected():
                break
            _audits = db.query(Audit.id, Audit.when_date, Audit.what, Audit.thing_type, Audit.thing_id, Audit.username, Audit.audit_data).filter(Audit.id > checkpoint).order_by(Audit.id.desc()).all()
            db.commit()
            if len(_audits) > 0:
                checkpoint = _audits[0][0]
            for record in _audits:
                if record[6] is not None and record[3] == 'link':
                    v0_id = record[6].get("v0_id")
                    v0_type = record[6].get("v0_type")
                    v1_id = record[6].get("v1_id")
                    v1_type = record[6].get("v1_type")
                    yield json.dumps({'what': record[2], 'when': record[1].strftime('%Y-%m-%d %H:%M:%s'), 'element_type': record[3], 'element_id': record[4], 'username': record[5], 'v0_id': v0_id, 'v0_type': v0_type, 'v1_id': v1_id, 'v1_type': v1_type})
                elif record[3] == 'entry' and record[6] is not None:
                    # We need to get the entry target id and target type.
                    target_id = record[6].get("target_id")
                    target_type = record[6].get("target_type")
                    yield json.dumps({'what': record[2], 'when': record[1].strftime('%Y-%m-%d %H:%M:%s'), 'element_type': record[3], 'element_id': record[4], 'username': record[5], 'target_id': target_id, 'target_type': target_type})
                else:
                    yield json.dumps({'what': record[2], 'when': record[1].strftime('%Y-%m-%d %H:%M:%s'), 'element_type': record[3], 'element_id': record[4], 'username': record[5]})
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
