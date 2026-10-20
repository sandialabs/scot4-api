import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.publisher import (
    NatsPublisher,
    audit_subject,
    notification_broadcast_subject,
    notification_user_subject,
)


class RecordingPublisher(NatsPublisher):
    def __init__(self):
        self.published = []

    async def publish(self, subject: str, payload: bytes, *, queue_on_disconnect: bool = True) -> None:
        self.published.append((subject, payload, queue_on_disconnect))


def test_audit_subject_normalizes_tokens():
    assert audit_subject("Entry.Some Type", "assign some.user") == (
        "scot.irelement.entry.some_type.assign_some_user"
    )


def test_notification_subjects():
    assert notification_user_subject(123, "create") == "scot.notification.user.123.create"
    assert notification_user_subject(123, "update") == "scot.notification.user.123.update"
    assert notification_broadcast_subject("create") == "scot.notification.broadcast.create"


@pytest.mark.asyncio
async def test_process_to_publish_uses_scot_irelement_subject_and_keeps_payload_values():
    publisher = RecordingPublisher()
    audit = SimpleNamespace(
        when_date=datetime(2026, 7, 20, tzinfo=timezone.utc),
        username="alice",
        what="assign some.user",
        thing_type="Entry",
        thing_subtype="Some Type",
        thing_id=42,
    )

    await publisher.processToPublish(audit)

    assert len(publisher.published) == 1
    subject, payload, queue_on_disconnect = publisher.published[0]
    assert subject == "scot.irelement.entry.some_type.assign_some_user"
    assert queue_on_disconnect is True
    payload_json = json.loads(payload)
    assert payload_json["what"] == "assign some.user"
    assert payload_json["element_type"] == "Entry.Some Type"
    assert payload_json["username"] == "alice"


@pytest.mark.asyncio
async def test_process_to_publish_suppresses_notification_audits():
    publisher = RecordingPublisher()
    audit = SimpleNamespace(
        when_date=datetime(2026, 7, 20, tzinfo=timezone.utc),
        username="alice",
        what="create",
        thing_type="notification",
        thing_subtype=None,
        thing_id=123,
    )

    await publisher.processToPublish(audit)

    assert publisher.published == []


@pytest.mark.asyncio
async def test_user_notification_refresh_payload_is_json_serializable():
    publisher = RecordingPublisher()

    await publisher.publish_user_notification_refresh(123, 456, "update", {"ack": True})

    assert len(publisher.published) == 1
    subject, payload, queue_on_disconnect = publisher.published[0]
    assert subject == "scot.notification.user.123.update"
    assert queue_on_disconnect is True
    payload_json = json.loads(payload)
    assert payload_json["what"] == "update"
    assert datetime.fromisoformat(payload_json["when"]).tzinfo is not None
    assert payload_json["element_type"] == "notification"
    assert payload_json["element_id"] == 456
    assert payload_json["user_id"] == 123
    assert payload_json["data"]["ack"] == True


@pytest.mark.asyncio
async def test_broadcast_notification_refresh_payload_is_json_serializable():
    publisher = RecordingPublisher()

    await publisher.publish_broadcast_notification_refresh("create", None)

    assert len(publisher.published) == 1
    subject, payload, queue_on_disconnect = publisher.published[0]
    assert subject == "scot.notification.broadcast.create"
    assert queue_on_disconnect is True
    payload_json = json.loads(payload)
    assert payload_json["what"] == "create"
    assert datetime.fromisoformat(payload_json["when"]).tzinfo is not None
    assert payload_json["element_type"] == "notification"
    assert payload_json["broadcast"] is True
