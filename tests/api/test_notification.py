from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings

from tests.utils.notification import create_random_notification


def test_read_notifications(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    notification = create_random_notification(db, faker, user.id)

    r = client.get(
        f"{settings.API_V1_STR}/notification",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    notification_data = r.json()
    assert notification_data is not None
    assert notification_data["totalCount"] == 0
    assert notification_data["resultCount"] == 0
    assert len(notification_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/notification",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    notification_data = r.json()
    assert notification_data is not None
    assert notification_data["totalCount"] == 1
    assert notification_data["resultCount"] == 1
    assert notification_data["result"][0]["id"] == notification.id


def test_ack_notifications(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    notification = create_random_notification(db, faker, user.id)

    r = client.post(
        f"{settings.API_V1_STR}/notification/ack/",
        headers=superuser_token_headers,
        json={"notification_ids": [notification.id]}
    )

    assert r.status_code == 200
    assert r.json() == [notification.id]

    r = client.post(
        f"{settings.API_V1_STR}/notification/ack/",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422
