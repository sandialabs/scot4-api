import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.enums import TargetTypeEnum, UserLinkEnum
from tests.utils.entry import create_random_entry
from tests.utils.user_links import create_random_user_links


def test_get_user_links(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user_links = create_random_user_links(db, faker)
    r = client.get(
        f"{settings.API_V1_STR}/user_links/{user_links.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == user_links.id

    r = client.get(
        f"{settings.API_V1_STR}/user_links/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/user_links/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_create_user_links(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    user = crud.user.get_by_username(db, username=settings.EMAIL_TEST_USER)
    entry = create_random_entry(db, faker)

    data = {
        "target_type": TargetTypeEnum.entry.value,
        "target_id": entry.id,
        "link_type": UserLinkEnum.favorite.value,
        "owner_id": user.id,
    }

    r = client.post(
        f"{settings.API_V1_STR}/user_links/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] is not None
    assert r.json()["owner_id"] == data["owner_id"]


def test_update_user_links(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    user_links = create_random_user_links(db, faker, owner=user)
    data = {
        "target_type": random.choice(list(TargetTypeEnum)).value,
    }

    r = client.put(
        f"{settings.API_V1_STR}/user_links/{user_links.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 422

    data = {
        "link_type": random.choice(list(UserLinkEnum)).value,
    }

    r = client.put(
        f"{settings.API_V1_STR}/user_links/{user_links.id}",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/user_links/{user_links.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["link_type"] == data["link_type"]

    r = client.put(
        f"{settings.API_V1_STR}/user_links/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/user_links/{user_links.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422


def test_delete_user_links(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    user_links = create_random_user_links(db, faker, owner=user)

    r = client.delete(
        f"{settings.API_V1_STR}/user_links/{user_links.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/user_links/{user_links.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == user_links.id

    r = client.get(
        f"{settings.API_V1_STR}/user_links/{user_links.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/user_links/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_favorite(client: TestClient, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    entry = create_random_entry(db, faker, user)

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/favorite", headers=superuser_token_headers
    )

    assert r.status_code == 200

    assert r.json() is not None
    assert r.json()["id"] == entry.id
    assert r.json()["favorite"] == True

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/favorite", headers=superuser_token_headers
    )

    assert r.status_code == 200

    assert r.json() is not None
    assert r.json()["id"] == entry.id
    assert r.json()["favorite"] == False
