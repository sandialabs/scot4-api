import datetime

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.user import create_random_user
from tests.utils.handler import create_random_handler


def test_get_handler(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    handler = create_random_handler(db, faker, user.username)

    r = client.get(
        f"{settings.API_V1_STR}/handler/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/handler/{handler.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    handler_get = r.json()
    assert handler_get is not None
    assert handler_get["id"] == handler.id


def test_create_handler(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    start_date = faker.date_time_this_month()

    data = {
        "start_date": start_date.isoformat(),
        "end_date": (start_date + datetime.timedelta(days=7)).isoformat(),
        "username": user.username,
        "position": faker.word()
    }

    r = client.post(
        f"{settings.API_V1_STR}/handler",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    handler_data = r.json()
    assert handler_data is not None
    assert handler_data["id"] > 0

    r = client.post(
        f"{settings.API_V1_STR}/handler",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_handler(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    handler = create_random_handler(db, faker, user.username)

    data = {
        "position": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/handler/{handler.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    handler_update = r.json()
    assert handler_update is not None
    assert handler_update["id"] == handler.id
    assert handler_update["position"] != handler.position
    assert handler_update["position"] == data["position"]

    r = client.put(
        f"{settings.API_V1_STR}/handler/{handler.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_delete_handler(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    handler = create_random_handler(db, faker, user.username)

    r = client.delete(
        f"{settings.API_V1_STR}/handler/{handler.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    handler_delete = r.json()
    assert handler_delete is not None
    assert handler_delete["id"] == handler.id

    r = client.get(
        f"{settings.API_V1_STR}/handler/{handler_delete['id']}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_date_range_handler(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    handler = create_random_handler(db, faker, user.username)

    r = client.get(
        f"{settings.API_V1_STR}/handler?start_date={handler.start_date.isoformat().split('+')[0]}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    handlers = r.json()
    assert handlers is not None
    assert handlers["totalCount"] >= 1
    assert handlers["resultCount"] >= 1
    assert any(i["id"] == handler.id for i in handlers["result"])
