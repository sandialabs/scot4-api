from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user
from tests.utils.apikey import create_apikey


def test_read_apikeys(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/apikey/",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    api_data = r.json()
    assert api_data["totalCount"] == 0
    assert api_data["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/apikey/",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_data = r.json()
    assert api_data["totalCount"] == 1
    assert api_data["resultCount"] == 1
    assert api_data["result"][0]["key"] == settings.FIRST_SUPERUSER_APIKEY


def test_create_apikey(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/apikey/",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    created_apikey = r.json()
    assert created_apikey["active"]

    # Make a role and assign to user
    role = create_random_role(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=superuser_token_headers,
        params={
            "username": settings.EMAIL_TEST_USER,
            "role_id": role.id
        },
    )

    r = client.post(
        f"{settings.API_V1_STR}/apikey/",
        headers=normal_user_token_headers,
        json=[role.name]
    )

    assert r.status_code == 200
    created_apikey = r.json()
    assert len(created_apikey["roles"]) == 1
    assert role.id == created_apikey["roles"][0]["id"]
    assert created_apikey["active"]

    r = client.post(
        f"{settings.API_V1_STR}/apikey/",
        headers=normal_user_token_headers,
        json=[-1]
    )

    assert r.status_code == 422


def test_update_apikey(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    apikey = create_apikey(db, faker, user.username)

    data = {"active": False}

    r = client.put(
        f"{settings.API_V1_STR}/apikey/{apikey.key}",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/apikey/-1",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 404

    data = {"active": False}
    r = client.put(
        f"{settings.API_V1_STR}/apikey/{apikey.key}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    api_data = r.json()
    assert apikey.key == api_data["key"]
    assert api_data["active"] is False
    assert apikey.owner == user.username

    data = {"roles": [-1]}
    r = client.put(
        f"{settings.API_V1_STR}/apikey/{apikey.key}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 422

    data = {"roles": ["testing role name"]}
    r = client.put(
        f"{settings.API_V1_STR}/apikey/{apikey.key}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 422

    role = create_random_role(db, faker)

    data = {"roles": [role.id]}
    r = client.put(
        f"{settings.API_V1_STR}/apikey/{apikey.key}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200


def test_get_apikey(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    apikey = create_apikey(db, faker, user.username)

    r = client.get(
        f"{settings.API_V1_STR}/apikey/{apikey.key}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/apikey/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/apikey/{apikey.key}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert apikey.key == r.json()["key"]
    assert apikey.owner == user.username


def test_delete_apikey(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    apikey = create_apikey(db, faker, user.username)

    r = client.delete(
        f"{settings.API_V1_STR}/apikey/{apikey.key}", headers=superuser_token_headers
    )
    assert 200 <= r.status_code < 300
    assert apikey.key == r.json()["key"]
    assert apikey.owner == user.username
    r = client.get(
        f"{settings.API_V1_STR}/apikey/{apikey.key}", headers=superuser_token_headers
    )
    assert 400 <= r.status_code < 500
    assert r.json()["detail"] == "Api key not found"
