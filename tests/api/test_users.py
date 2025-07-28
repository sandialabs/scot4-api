from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.user import create_random_user


def test_get_users(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    users_data = r.json()
    assert users_data["totalCount"] >= 1
    assert users_data["resultCount"] >= 1
    assert any(i["id"] == user.id for i in users_data["result"])


def read_usernames(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/users/usernames",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    users_data = r.json()
    assert users_data["totalCount"] >= 1
    assert users_data["resultCount"] >= 1
    assert any(i == user.username for i in users_data["results"])


def test_create_user(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    data = {
        "username": f"{faker.unique.word()}_{faker.pyint()}",
        "password": faker.password()
    }

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    user_data = r.json()
    assert user_data is not None
    assert user_data["id"] >= 0
    assert user_data["username"] == data["username"]

    r = client.post(
        f"{settings.API_V1_STR}/users/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 400


def test_update_user_me(client: TestClient, normal_user_token_headers: dict, faker: Faker) -> None:
    data = {
        "fullname": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    user_data = r.json()
    assert user_data is not None
    assert user_data["fullname"] != data["fullname"]

    r = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    user_data = r.json()
    assert user_data is not None
    assert user_data["fullname"] == data["fullname"]


def test_read_user_who_am_i(client: TestClient, superuser_token_headers: dict) -> None:
    r = client.put(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    user_data = r.json()
    assert user_data is not None
    assert user_data["is_active"] is True
    assert user_data["is_superuser"]
    assert user_data["email"] == settings.FIRST_SUPERUSER


def test_create_user_open(client: TestClient, faker: Faker) -> None:
    data = {
        "username": faker.word(),
        "password": faker.password(),
        "email": faker.email(),
        "fullname": faker.word()
    }

    r = client.post(
        f"{settings.API_V1_STR}/users/open",
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/users/open",
        json=data
    )

    assert r.status_code == 403


def test_read_user(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 400

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.username}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 400

    r = client.get(
        f"{settings.API_V1_STR}/users/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/users/{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    user_data = r.json()
    assert user_data["id"] == user.id

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.username}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    user_data = r.json()
    assert user_data["username"] == user.username


def test_update_user(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    data = {
        "fullname": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/users/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    user_data = r.json()
    assert user_data["id"] == user.id
    assert user_data["fullname"] == data["fullname"]


def test_delete_user(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/users/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    user_data = r.json()
    assert user_data["id"] == user.id

    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_reset_failed_attempts(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker, failed_attempts=10)

    r = client.post(
        f"{settings.API_V1_STR}/users/{user.username}/reset-failed-attempts",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/users/{faker.word()}/reset-failed-attempts",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/users/{user.username}/reset-failed-attempts",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json()["msg"] == "Password attempts for user %s reset successfully" % user.username
