import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

import nats
from nats.aio.client import Client as NATS

from app.core.config import settings

if TYPE_CHECKING:
    from app.schemas.audit import AuditCreate

log = logging.getLogger(__name__)


UNSAFE_SUBJECT_TOKEN_CHARS = re.compile(r"[^a-z0-9_-]+")


def subject_token(value: object) -> str:
    token = UNSAFE_SUBJECT_TOKEN_CHARS.sub("_", str(value).strip().lower()).strip("_")
    return token or "unknown"


def subject_path(*tokens: object) -> str:
    return ".".join(subject_token(token) for token in tokens)


def audit_subject(element_type: object, what: object) -> str:
    element_tokens = str(element_type).split(".")
    return subject_path(settings.NATS_SUBJECT_ROOT, "irelement", *element_tokens, what)


def notification_user_subject(user_id: object, what: object) -> str:
    return subject_path(settings.NATS_SUBJECT_ROOT, "notification", "user", user_id, what)


def notification_broadcast_subject(what: object) -> str:
    return subject_path(settings.NATS_SUBJECT_ROOT, "notification", "broadcast", what)


@dataclass(frozen=True)
class QueuedPublish:
    subject: str
    payload: bytes


class NatsPublisher:
    def __init__(
        self,
        servers: list[str],
        *,
        name: str = "scot-api",
        connect_timeout: float = 5,
        reconnect_time_wait: float = 2,
        max_reconnect_attempts: int = -1,
        enabled: bool = True,
        max_queue_size: int = 10_000,
        backlog_batch_size: int = 20,
        backlog_drain_interval: float = 0.2,
        drop_log_interval: float = 60,
    ):
        self.servers = servers
        self.name = name
        self.connect_timeout = connect_timeout
        self.reconnect_time_wait = reconnect_time_wait
        self.max_reconnect_attempts = max_reconnect_attempts
        self.enabled = enabled and (not settings.TEST)
        self.max_queue_size = max_queue_size
        self.backlog_batch_size = backlog_batch_size
        self.backlog_drain_interval = backlog_drain_interval
        self.drop_log_interval = drop_log_interval
        self.nc: Optional[NATS] = None
        self._connect_lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None
        self._drain_task: Optional[asyncio.Task] = None
        self._backlog: asyncio.Queue[QueuedPublish] = asyncio.Queue(maxsize=max_queue_size)
        self._stopping = False
        self._suppress_closed_cb = False
        self._dropped_since_log = 0
        self._total_dropped_while_full = 0
        self._last_drop_log = 0.0

    async def _connect(self) -> bool:
        async def disconnected_cb():
            log.info("NATS disconnected, waiting for reconnect")

        async def reconnected_cb():
            log.info("NATS reconnected")
            self._schedule_backlog_drain()

        async def closed_cb():
            log.info("NATS connection closed, scheduling reconnect")
            self.nc = None
            if not self._stopping and not self._suppress_closed_cb:
                self._schedule_reconnect()

        async def error_cb(e: Exception):
            log.exception("NATS error: %r", e)

        nc = await nats.connect(
            servers=self.servers,
            name=self.name,
            connect_timeout=self.connect_timeout,
            reconnect_time_wait=self.reconnect_time_wait,
            max_reconnect_attempts=self.max_reconnect_attempts,
            disconnected_cb=disconnected_cb,
            reconnected_cb=reconnected_cb,
            closed_cb=closed_cb,
            error_cb=error_cb,
            user=settings.NATS_USERNAME,
            password=settings.NATS_PASSWORD,
        )
        self.nc = nc
        log.info("Connected to NATS: %s", self.nc.connected_url.netloc)
        self._schedule_backlog_drain()
        return True

    async def ensure_connected(self) -> bool:
        if not self.enabled:
            return False

        current = self.nc
        if current and not current.is_closed and current.is_connected:
            return True

        async with self._connect_lock:
            current = self.nc
            if current and not current.is_closed and current.is_connected:
                return True

            if current and not current.is_closed and getattr(current, "is_reconnecting", False):
                return False

            if current and not current.is_closed:
                self._suppress_closed_cb = True
                try:
                    await current.close()
                except Exception:
                    log.exception("Failed to close stale NATS client")
                finally:
                    self._suppress_closed_cb = False
                self.nc = None

            try:
                return await self._connect()
            except Exception:
                log.exception("Failed to connect to NATS")
                self.nc = None
                return False

    async def _reconnect_loop(self) -> None:
        try:
            while not self._stopping:
                if await self.ensure_connected():
                    return
                await asyncio.sleep(self.reconnect_time_wait)
        except asyncio.CancelledError:
            return

    def _schedule_reconnect(self) -> None:
        if self._stopping:
            return
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    def _schedule_backlog_drain(self) -> None:
        if self._stopping or self._backlog.empty():
            return
        if self._drain_task and not self._drain_task.done():
            return
        self._drain_task = asyncio.create_task(self._drain_backlog())

    def _log_queue_full_drop(self, subject: str) -> None:
        self._dropped_since_log += 1
        self._total_dropped_while_full += 1
        now = time.monotonic()
        if self._last_drop_log == 0.0 or now - self._last_drop_log >= self.drop_log_interval:
            log.warning(
                "NATS backlog queue full; dropped %s unpublished audit events since last warning "
                "(total_dropped_while_full=%s, queue_size=%s, subject=%s)",
                self._dropped_since_log,
                self._total_dropped_while_full,
                self._backlog.qsize(),
                subject,
            )
            self._dropped_since_log = 0
            self._last_drop_log = now

    def _reset_drop_tracking_if_needed(self) -> None:
        if self._total_dropped_while_full:
            log.warning(
                "NATS backlog queue recovered; total dropped while full=%s",
                self._total_dropped_while_full,
            )
        self._dropped_since_log = 0
        self._total_dropped_while_full = 0
        self._last_drop_log = 0.0

    def _enqueue_backlog(self, subject: str, payload: bytes) -> bool:
        try:
            self._backlog.put_nowait(QueuedPublish(subject=subject, payload=payload))
        except asyncio.QueueFull:
            self._log_queue_full_drop(subject)
            return False
        return True

    async def _publish_now(self, subject: str, payload: bytes) -> None:
        await self.nc.publish(subject, payload)

    async def _drain_backlog(self) -> None:
        try:
            while not self._stopping and not self._backlog.empty():
                if not await self.ensure_connected():
                    self._schedule_reconnect()
                    return

                published_count = 0
                for _ in range(self.backlog_batch_size):
                    try:
                        queued = self._backlog.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    try:
                        await self._publish_now(queued.subject, queued.payload)
                    except Exception:
                        log.exception("Failed to publish queued NATS subject=%s", queued.subject)
                        self._schedule_reconnect()
                        if not self._enqueue_backlog(queued.subject, queued.payload):
                            log.warning(
                                "Failed queued NATS publish could not be requeued: subject=%s",
                                queued.subject,
                            )
                        return
                    else:
                        published_count += 1
                    finally:
                        self._backlog.task_done()

                if self._backlog.empty():
                    log.info("NATS backlog drain complete")
                    self._reset_drop_tracking_if_needed()
                    return

                if published_count:
                    await asyncio.sleep(self.backlog_drain_interval)
        except asyncio.CancelledError:
            return

    async def start(self) -> None:
        if not self.enabled:
            log.info("NATS publisher disabled")
            return

        self._stopping = False
        await self.ensure_connected()

    async def stop(self) -> None:
        self._stopping = True
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        self._reconnect_task = None

        if self._drain_task and not self._drain_task.done():
            self._drain_task.cancel()
            try:
                await self._drain_task
            except asyncio.CancelledError:
                pass
        self._drain_task = None

        if self.nc and not self.nc.is_closed:
            await self.nc.drain()
        self.nc = None

    async def publish(self, subject: str, payload: bytes, *, queue_on_disconnect: bool = True) -> None:
        if not self.enabled:
            return
        if queue_on_disconnect and not self._backlog.empty():
            if self._enqueue_backlog(subject, payload):
                self._schedule_backlog_drain()
            return

        if not await self.ensure_connected():
            if queue_on_disconnect:
                if self._enqueue_backlog(subject, payload):
                    log.warning(
                        "NATS publish queued (not connected): subject=%s queue_size=%s",
                        subject,
                        self._backlog.qsize(),
                    )
                    self._schedule_reconnect()
            else:
                log.warning("NATS publish dropped (not connected): subject=%s", subject)
            return

        try:
            await self._publish_now(subject, payload)
        except Exception:
            log.exception("Failed to publish to NATS subject=%s", subject)
            if queue_on_disconnect:
                self._enqueue_backlog(subject, payload)
            self._schedule_reconnect()

    async def processToPublish(self, content: "AuditCreate") -> None:
        # get crucial metadata to fail fast if missing
        element_type = getattr(content, "thing_type", None)
        what = getattr(content, "what", None)

        # if the element_type is in this list, we don't publish
        # these element_types serve no purpose for nats subscribers
        element_type_ignore_list = [
            "notification",
            "appearance",
            "permission"  # in ignore list because handled in different process
        ]

        # verify we have anything worth publishing
        if not element_type or not what:
            return
        if what == "read":
            return
        if subject_token(element_type) in element_type_ignore_list:
            return

        # get rest of necessary metadata
        element_subtype = getattr(content, "thing_subtype", None)
        if element_subtype:
            element_type += f".{element_subtype}"
        when = getattr(content, "when_date", None)
        when_str = when.isoformat() if when else None
        element_id = getattr(content, "thing_id", None)
        username = getattr(content, "username", None)
        audit_data = getattr(content, "audit_data", None)

        # build the minimal payload
        payload_json = {
            "what": what, 
            "when": when_str, 
            "element_type": element_type, 
            "element_id": element_id, 
            "username": username
        }

        # Want to include v0 and v1 info if element_type link
        if element_type == "link" and audit_data is not None:
            payload_json["v0_id"] = audit_data.get("v0_id")
            payload_json["v0_type"] = audit_data.get("v0_type")
            payload_json["v1_id"] = audit_data.get("v1_id")
            payload_json["v1_type"] = audit_data.get("v1_type")
        # Want to include target id / type if element_type entry
        elif element_type == "entry" and audit_data is not None:
            payload_json["target_id"] = audit_data.get("target_id")
            payload_json["target_type"] = audit_data.get("target_type")
        # Want to include entity id if element_type enrichment
        elif element_type == "enrichment" and audit_data is not None:
            payload_json["entity_id"] = audit_data.get("entity_id")

        # encode json payload and publish
        payload = json.dumps(payload_json).encode("utf-8")
        subject = audit_subject(element_type, what)

        # only put publish on the disconnect queue if it isn't a read
        await self.publish(subject, payload, queue_on_disconnect=(what != "read"))

    async def publish_user_notification_refresh(self, user_id: int, notification_id: int, what: str, data: any) -> None:
        # fast exit on what: read
        if what == "read":
            return
        payload_json = {
            "what": what, 
            "when": datetime.now(timezone.utc).isoformat(),
            "element_type": "notification",
            "element_id": notification_id,
            "user_id": user_id
        }
        if data is not None:
            payload_json["data"] = data
        payload = json.dumps(payload_json).encode("utf-8")
        await self.publish(notification_user_subject(user_id, what), payload)

    async def publish_broadcast_notification_refresh(self, what: str, data: any) -> None:
        # fast exit on what: read
        if what == "read":
            return
        payload_json = {
            "what": what, 
            "when": datetime.now(timezone.utc).isoformat(),
            "element_type": "notification",
            "broadcast": True
        }
        if data is not None:
            payload_json["data"] = data
        payload = json.dumps(payload_json).encode("utf-8")
        await self.publish(notification_broadcast_subject(what), payload)
