from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_update_role(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)

    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/role/{role.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/role/{role.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/role/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/role/{role.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    role_data = r.json()
    assert role_data is not None
    assert role_data["id"] == role.id
    assert role_data["description"] == data["description"]


def test_create_role(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    data = {
        "name": f"{faker.unique.word()}_{faker.pyint()}",
        "description": faker.sentence(12)
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/role/",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/role/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    created_role = r.json()
    assert created_role["name"] == data["name"]
    assert created_role["description"] == data["description"]


def test_get_role(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/role/{role.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/role/{role.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_role = r.json()
    assert api_role["name"] == role.name
    assert api_role["description"] == role.description

    r = client.get(
        f"{settings.API_V1_STR}/role/-1",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


def test_get_roles(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/role",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    role_data = r.json()
    assert role_data is not None
    assert role_data["totalCount"] >= 1
    assert role_data["resultCount"] >= 1
    assert any(i["id"] == role.id for i in role_data["result"])


def test_delete_role(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/role/{role.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/role/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/role/{role.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    role_data = r.json()
    assert role_data["id"] == role.id

    r = client.delete(
        f"{settings.API_V1_STR}/role/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_assign_role(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    role1 = create_random_role(db, faker)
    role2 = create_random_role(db, faker)
    user = create_random_user(db, faker)
    assert role1 not in user.roles
    assert role2 not in user.roles

    data = {
        "username": user.username
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 422

    data = {
        "role_id": role1.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 422

    # Try with nonexistent role
    data = {
        "username": user.username,
        "role_id": -1
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 404

    # Try with nonexistent user
    data = {
        "username": f"{faker.word()}-test",
        "role_id": role1.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 404

    # Assign by id
    data = {
        "username": user.username,
        "role_id": role1.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 200
    assert r.json()["msg"] == "Success: role %s was assigned to %s" % (role1.name, user.username)

    # Assign by name
    data = {
        "username": user.username,
        "role_name": role2.name
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 200
    assert r.json()["msg"] == "Success: role %s was assigned to %s" % (role2.name, user.username)

    # Granting a role the user already has should raise an exception
    data = {
        "username": user.username,
        "role_name": role1.name
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 400

    # User must be superuser
    r = client.post(
        f"{settings.API_V1_STR}/role/assign",
        headers=normal_user_token_headers,
        params=data,
    )

    assert r.status_code == 403


def test_remove_role(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    role1 = create_random_role(db, faker)
    role2 = create_random_role(db, faker)
    user1 = create_user_with_role(db, role1, faker)
    user2 = create_user_with_role(db, role2, faker)
    assert role1 in user1.roles
    assert role2 in user2.roles

    # Remove by id
    data = {
        "username": user1.username,
        "role_id": role1.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/remove",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 200
    assert r.json()["msg"] == "Success: role %s was removed from %s" % (role1.name, user1.username)

    # Remove by name
    data = {
        "username": user2.username,
        "role_name": role2.name
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/remove",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 200
    assert r.json()["msg"] == "Success: role %s was removed from %s" % (role2.name, user2.username)

    # Omit role id/name
    data = {
        "username": user1.username
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/remove",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 422

    # Omit username
    data = {
        "role_id": role1.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/remove",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 422

    # Try with nonexistent role
    data = {
        "username": user1.username,
        "role_id": -1
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/remove",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 404

    # Try with nonexistent user
    data = {
        "username": faker.word(),
        "role_id": role1.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/remove",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 404

    # Removing a role that does not exist should raise an exception
    data = {
        "username": user2.username,
        "role_name": role1.name
    }

    r = client.post(
        f"{settings.API_V1_STR}/role/remove",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 400

    # User must be superuser
    r = client.post(
        f"{settings.API_V1_STR}/role/remove",
        headers=normal_user_token_headers,
        params=data,
    )

    assert r.status_code == 403
