from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import PermissionEnum, TargetTypeEnum
from tests.utils.roles import create_random_role
from tests.utils.user import create_user_with_role
from tests.utils.alert import create_random_alert
from tests.utils.permission import create_random_permission


def test_grant_permission(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, user.username)

    data = {
        "role_id": role.id,
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id,
        "permission": PermissionEnum.read.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/permissions/grant",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/permissions/grant",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/permissions/grant",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    permission_data = r.json()
    assert permission_data is not None
    assert permission_data["permission"] == PermissionEnum.read.value
    assert permission_data["target_id"] == alert.id

    # Grant modify permission
    data = {
        "role_id": role.id,
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id,
        "permission": PermissionEnum.modify.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/permissions/grant",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    permission_data = r.json()
    assert permission_data is not None
    assert permission_data["permission"] == PermissionEnum.modify.value
    assert permission_data["target_id"] == alert.id

    # Re-assigning a permission is a no-op
    r = client.post(
        f"{settings.API_V1_STR}/permissions/grant",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    permission_data = r.json()
    assert permission_data is not None
    assert permission_data["permission"] == PermissionEnum.modify.value
    assert permission_data["target_id"] == alert.id

    data = {
        "role_id": role.id,
        "target_type": TargetTypeEnum.alert.value,
        "target_id": -1,
        "permission": PermissionEnum.delete.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/permissions/grant",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 422


def test_revoke_permission(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, user.username)
    permission = create_random_permission(db, role, alert)

    data = {
        "role_id": role.id,
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id,
        "permission": PermissionEnum.admin.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/permissions/revoke",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 403

    data = {
        "role_id": role.id,
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id,
        "permission": permission.permission.value,
    }

    r = client.post(
        f"{settings.API_V1_STR}/permissions/revoke",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/permissions/revoke",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/permissions/revoke",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 204

    # Re-revoking a permission should produce an execption
    r = client.post(
        f"{settings.API_V1_STR}/permissions/revoke",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/permissions/revoke",
        headers=superuser_token_headers,
        json=data,
    )


def test_set_permission(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, user.username)

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id,
        "permissions": {
            PermissionEnum.admin.value: [role.id],
            PermissionEnum.read.value: [role.id],
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/permissions/set",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id,
        "permissions": {
            PermissionEnum.read.value: [role.id],
            PermissionEnum.modify.value: [role.id],
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/permissions/set",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/permissions/set",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    permission_data = r.json()
    assert permission_data is not None
    assert PermissionEnum.modify.value in permission_data.keys()
    assert PermissionEnum.read.value in permission_data.keys()


def test_get_permission_roles(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    role1 = create_random_role(db, faker)
    role2 = create_random_role(db, faker)
    user = create_user_with_role(db, [role1, role2], faker)
    alert = create_random_alert(db, faker, user.username)
    permission = create_random_permission(db, [role1, role2], alert)

    # Get data
    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id
    }

    r = client.get(
        f"{settings.API_V1_STR}/permissions/getroles",
        headers=normal_user_token_headers,
        params=data,
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/permissions/getroles",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/permissions/getroles",
        headers=superuser_token_headers,
        params=data,
    )

    assert r.status_code == 200
    permissions = r.json()
    assert permissions is not None
    assert permission.permission.value in permissions.keys()
