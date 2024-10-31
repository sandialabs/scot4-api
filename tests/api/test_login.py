import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.user import create_random_user


def test_login_local(client: TestClient, faker: Faker, db: Session) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }

    r = client.post(
        f"{settings.API_V1_STR}/login/local",
        data=login_data
    )

    assert r.status_code == 200
    login_data == r.json()
    assert login_data is not None
    assert login_data["username"] == settings.FIRST_SUPERUSER_USERNAME
    assert login_data["password"] == settings.FIRST_SUPERUSER_PASSWORD

    login_data = {
        "username": faker.word(),
        "password": faker.password(),
    }

    r = client.post(
        f"{settings.API_V1_STR}/login/local",
        data=login_data
    )

    assert r.status_code == 401

    password = faker.password()
    user = create_random_user(db, faker, password=password, is_active=False)

    login_data = {
        "username": user.username,
        "password": password,
    }

    r = client.post(
        f"{settings.API_V1_STR}/login/local",
        data=login_data
    )

    assert r.status_code == 400


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }

    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data
    )

    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens["access_token"]

    r2 = client.get(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer " + tokens["access_token"]},
    )

    assert r.status_code == 200
    assert r2.json()["username"] == login_data["username"]


def test_get_access_token_with_roles(client: TestClient, faker: Faker) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
        "scope": "admin",
    }

    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data
    )

    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens["access_token"]

    r2 = client.get(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer " + tokens["access_token"]},
    )

    assert r.status_code == 200
    assert r2.json()["username"] == login_data["username"]

    login_data["scope"] = faker.word()
    r3 = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)

    assert r3.status_code == 403


def test_bad_username_password(client: TestClient, faker: Faker) -> None:
    login_data = {
        "username": faker.word(),
        "password": faker.word()
    }

    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data=login_data
    )

    assert r.status_code == 401


def test_bad_token(client: TestClient) -> None:
    randToken = hex(random.getrandbits(512))[2:]
    r = client.get(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer " + randToken},
    )

    assert r.status_code == 401


def test_logout(client: TestClient, normal_user_token_headers: dict) -> None:
    randToken = hex(random.getrandbits(512))[2:]
    r = client.get(
        f"{settings.API_V1_STR}/logout",
        headers={"Authorization": "Bearer " + randToken},
    )

    assert r.status_code == 200
    assert r.json()["msg"] == "Not logged in"

    r = client.get(
        f"{settings.API_V1_STR}/logout",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["msg"] == "Logout Successful"
