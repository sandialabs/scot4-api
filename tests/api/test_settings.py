from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import AuthTypeEnum, StorageProviderEnum
from app.core.config import settings

from tests.utils.settings import create_random_setting, create_random_auth_setting, create_random_storage_provider


def test_update_setting(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    create_random_setting(db, faker)

    data = {
        "site_name": f"{faker.word()}_{faker.pyint()}"
    }

    r = client.put(
        f"{settings.API_V1_STR}/settings",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/settings",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/settings",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert setting_data["site_name"] == data["site_name"]


def test_read_setting(client: TestClient, normal_user_token_headers: dict) -> None:
    # don't need to create random settings since there are default ones applied when creating the server
    r = client.get(
        f"{settings.API_V1_STR}/settings",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert setting_data["id"] == 1


def test_read_auth_methods(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    auth = create_random_auth_setting(db, faker)
    r = client.get(
        f"{settings.API_V1_STR}/settings/auth",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/settings/auth",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert any(auth.id == i["id"] for i in setting_data)


def test_create_auth_method(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    data = {
        "auth": AuthTypeEnum.local.value,
        "auth_properties": {
            "provider_name": faker.word()
        },
        "auth_active": faker.pybool()
    }

    r = client.post(
        f"{settings.API_V1_STR}/settings/auth",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/settings/auth",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/settings/auth",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    settings_data = r.json()
    assert settings_data["id"] >= 1
    assert settings_data["auth"] == data["auth"]
    assert settings_data["auth_properties"] == data["auth_properties"]


def test_update_auth_method(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    auth = create_random_auth_setting(db, faker)
    data = {
        "auth_properties": {
            "provider_name": faker.word()
        }
    }

    r = client.put(
        f"{settings.API_V1_STR}/settings/auth/{auth.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/settings/auth/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/settings/auth/{auth.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/settings/auth/{auth.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    settings_data = r.json()
    assert settings_data["id"] == auth.id
    assert settings_data["auth_properties"] == data["auth_properties"]
    assert settings_data["auth_properties"] != auth.auth_properties


def test_delete_auth_method(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    auth = create_random_auth_setting(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/settings/auth/{auth.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/settings/auth/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/settings/auth/1",
        headers=superuser_token_headers
    )

    assert r.status_code == 400

    r = client.delete(
        f"{settings.API_V1_STR}/settings/auth/{auth.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    settings_data = r.json()
    assert settings_data["id"] == auth.id

    r = client.get(
        f"{settings.API_V1_STR}/settings/auth",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert auth.id not in [i["id"] for i in setting_data]


def test_get_auth_help(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/settings/auth/help",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/settings/auth/help",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert isinstance(setting_data, dict)


def test_read_storage_providers(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    storage = create_random_storage_provider(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/settings/storage_provider",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/settings/storage_provider",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert any(storage.id == i["id"] for i in setting_data)


def test_read_storage_provider(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    storage = create_random_storage_provider(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/settings/storage_provider/{storage.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/settings/storage_provider/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/settings/storage_provider/{storage.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert setting_data["id"] == storage.id


def test_create_storage_provider(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    path = faker.file_path().rsplit("/", 1)[0]
    data = {
        "provider": StorageProviderEnum.disk.value,
        "config": {
            "provider_name": faker.word(),
            "root_directory": path,
            "deleted_items_directory": f"{path}_deleted"
        },
        "enabled": faker.pybool()
    }

    r = client.post(
        f"{settings.API_V1_STR}/settings/storage_provider",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/settings/storage_provider",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/settings/storage_provider",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert setting_data["id"] >= 1
    assert setting_data["config"] == data["config"]


def test_update_storage_provider(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    storage = create_random_storage_provider(db, faker)
    path = faker.file_path().rsplit("/", 1)[0]
    data = {
        "config": {
            "provider_name": faker.word(),
            "root_directory": path,
            "deleted_items_directory": f"{path}_deleted"
        }
    }

    r = client.put(
        f"{settings.API_V1_STR}/settings/storage_provider/{storage.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/settings/storage_provider/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/settings/storage_provider/{storage.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/settings/storage_provider/{storage.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert setting_data["id"] == storage.id
    assert setting_data["config"] == data["config"]


def test_delete_storage_provider(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    storage = create_random_storage_provider(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/settings/storage_provider/{storage.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/settings/storage_provider/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/settings/storage_provider/{storage.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert setting_data["id"] == storage.id

    r = client.get(
        f"{settings.API_V1_STR}/settings/storage_provider/{storage.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_get_storage_provider_help(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/settings/storage_provider_help",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/settings/storage_provider_help",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    setting_data = r.json()
    assert setting_data is not None
    assert isinstance(setting_data, dict)
