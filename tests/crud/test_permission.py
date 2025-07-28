import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate

from tests.utils.alert import create_random_alert
from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.permission import create_random_permission
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    alert = create_random_alert(db, faker)
    permission = create_random_permission(db, role, alert)
    db_obj = crud.permission.get(db, permission.id)

    assert db_obj.id == permission.id

    db_obj = crud.permission.get(db, -1)

    assert db_obj is None


def test_get_multi_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    alert = create_random_alert(db, faker)
    permissions = []
    for _ in range(5):
        permissions.append(create_random_permission(db, role, alert))

    db_objs = crud.permission.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == permissions[0].id for i in db_objs)

    db_objs = crud.permission.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == permissions[1].id for i in db_objs)

    db_objs = crud.permission.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.permission.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, owner)
    permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert.id,
        permission=random.choice(list(PermissionEnum))
    )
    db_obj = crud.permission.create(db, obj_in=permission)

    assert db_obj.id is not None
    assert db_obj.role_id == permission.role_id
    assert db_obj.target_type == permission.target_type
    assert db_obj.target_id == permission.target_id
    assert db_obj.permission == permission.permission


def test_update_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, owner)
    permission = create_random_permission(db, role, alert)

    role1 = create_random_role(db, faker)
    alert1 = create_random_alert(db, faker, owner)
    update = PermissionUpdate(
        role_id=role1.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert1.id,
        permission=random.choice(list(PermissionEnum))
    )

    db_obj = crud.permission.update(db, db_obj=permission, obj_in=update)

    assert db_obj.id == permission.id
    assert db_obj.role_id == update.role_id
    assert db_obj.target_type == update.target_type
    assert db_obj.target_id == update.target_id
    assert db_obj.permission == update.permission

    update = {}

    db_obj = crud.permission.update(db, db_obj=permission, obj_in=update)

    assert db_obj.id == permission.id

    update = {
        "test": "test"
    }

    db_obj = crud.permission.update(db, db_obj=permission, obj_in=update)

    assert db_obj.id == permission.id
    assert not hasattr(db_obj, "test")

    role1 = create_random_role(db, faker)
    alert1 = create_random_alert(db, faker, owner)
    update = {
        "role_id": role1.id,
        "target_type": TargetTypeEnum.alert,
        "target_id": alert1.id,
        "permission": random.choice(list(PermissionEnum))
    }

    db_obj = crud.permission.update(db, db_obj=Permission(), obj_in=update)

    assert db_obj.id == permission.id + 1
    assert db_obj.role_id == update["role_id"]
    assert db_obj.target_type == update["target_type"]
    assert db_obj.target_id == update["target_id"]
    assert db_obj.permission == update["permission"]


def test_remove_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, owner)
    permission = create_random_permission(db, role, alert)

    db_obj = crud.permission.remove(db, _id=permission.id)

    assert db_obj.id == permission.id

    db_obj_del = crud.permission.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.permission.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, owner)
    permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert.id,
        permission=random.choice(list(PermissionEnum))
    )

    db_obj = crud.permission.get_or_create(db, obj_in=permission)

    assert db_obj.id is not None

    same_db_obj = crud.permission.get_or_create(db, obj_in=permission)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, role, faker)
    owner = create_random_user(db, faker)
    alert = create_random_alert(db, faker, owner)
    permissions = []
    for _ in range(5):
        permissions.append(create_random_permission(db, role, alert))

    random_permission = random.choice(permissions)

    db_obj, count = crud.permission.query_with_filters(db, filter_dict={"id": random_permission.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_permission.id

    db_obj, count = crud.permission.query_with_filters(db, filter_dict={"role_id": role.id})

    assert db_obj is not None
    assert len(db_obj) == len(permissions)
    assert len(db_obj) == count
    assert all(a.role_id == role.id for a in db_obj)

    db_obj, count = crud.permission.query_with_filters(db, filter_dict={"role_id": role.id}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(permissions) - 1
    assert len(db_obj) == count - 1
    assert all(a.role_id == role.id for a in db_obj)

    db_obj, count = crud.permission.query_with_filters(db, filter_dict={"role_id": role.id}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.role_id == role.id for a in db_obj)


def test_create_with_owner_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, owner)
    permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert.id,
        permission=random.choice(list(PermissionEnum))
    )
    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.permission.create_with_owner(db, obj_in=permission, owner=owner)

    assert db_obj is not None
    assert db_obj.role_id == permission.role_id
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, owner)
    permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert.id,
        permission=PermissionEnum.read
    )

    db_obj = crud.permission.create_with_permissions(db, obj_in=permission, perm_in={PermissionEnum.modify: [role.id]})

    assert db_obj.id is not None
    assert db_obj.role_id == permission.role_id
    assert db_obj.target_type == permission.target_type
    assert db_obj.target_id == permission.target_id
    assert db_obj.permission == permission.permission


def test_get_history_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, owner)
    permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert.id,
        permission=PermissionEnum.read
    )

    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.permission.create(db, obj_in=permission, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.permission.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_permission(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    role = create_random_role(db, faker)
    alert = create_random_alert(db, faker)
    permission = create_random_permission(db, role, alert)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.permission.remove(db, _id=permission.id, audit_logger=audit_logger)

    assert db_obj.id == permission.id

    db_obj = crud.permission.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_permission_from_roles(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    role = create_random_role(db, faker)
    alert = create_random_alert(db, faker, user)
    permission = create_random_permission(db, role, alert)

    db_obj = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.alert, alert.id)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0] == permission.permission


def test_get_permissions(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, user)
    permission = create_random_permission(db, role, alert)

    assert crud.permission.get_permissions(
        db, user.username, TargetTypeEnum.alert, alert.id
    ) == [permission.permission]


def test_user_is_admin(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    admin_permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.admin,
        target_id=0,
        permission=PermissionEnum.admin,
    )

    assert crud.permission.user_is_admin(db, user) is False

    crud.permission.grant_permission(db, admin_permission)

    assert crud.permission.user_is_admin(db, user) is True


def test_roles_have_admin(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    admin_permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.admin,
        target_id=0,
        permission=PermissionEnum.admin,
    )

    assert crud.permission.roles_have_admin(db, [role]) is False

    crud.permission.grant_permission(db, admin_permission)

    assert crud.permission.roles_have_admin(db, [role]) is True


def test_grant_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, user)
    read_permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert.id,
        permission=PermissionEnum.read,
    )
    modify_permission = PermissionCreate(
        role_id=role.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert.id,
        permission=PermissionEnum.modify,
    )

    crud.permission.grant_permission(db, read_permission)

    assert crud.permission.get_permissions(
        db, user.username, TargetTypeEnum.alert, alert.id
    ) == [PermissionEnum.read]

    # Double-granting a permission should do nothing
    crud.permission.grant_permission(db, read_permission)

    assert crud.permission.get_permissions(
        db, user.username, TargetTypeEnum.alert, alert.id
    ) == [PermissionEnum.read]

    crud.permission.grant_permission(db, modify_permission)
    permissions = crud.permission.get_permissions(
        db, user.username, TargetTypeEnum.alert, alert.id
    )

    assert len(permissions) == 2
    assert PermissionEnum.read in permissions
    assert PermissionEnum.modify in permissions


def test_revoke_permission(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, user)
    permission = create_random_permission(db, role, alert)

    crud.permission.revoke_permission(db, permission)
    assert crud.permission.get_permissions(
        db, user.username, TargetTypeEnum.alert, alert.id
    ) == []

    # Re-revoking a permissions should return None
    assert crud.permission.revoke_permission(db, permission) is None


def test_create_owner_permissions(db: Session, faker: Faker):
    role = create_random_role(db, faker)  # Role on both users
    role2 = create_random_role(db, faker)  # Role only on user 2
    user1 = create_user_with_role(db, role, faker)
    user2 = create_user_with_role(db, [role, role2], faker)
    alert = create_random_alert(db, faker, user1)

    crud.permission.create_owner_permissions(db, user1, TargetTypeEnum.alert, alert.id)

    permissions = crud.permission.get_permissions(db, user1.username, TargetTypeEnum.alert, alert.id)
    assert PermissionEnum.read in permissions
    assert PermissionEnum.modify in permissions
    assert PermissionEnum.delete in permissions
    assert len(permissions) == len(list(PermissionEnum)) - 1

    permissions = crud.permission.get_permissions(db, user2.username, TargetTypeEnum.alert, alert.id)
    assert PermissionEnum.read in permissions
    assert PermissionEnum.modify in permissions
    assert PermissionEnum.delete in permissions
    assert len(permissions) == 3

    # Having a read permission on a role for one alert causes all alerts created
    # by someone with that role to be readable by that role by default
    crud.permission.grant_permission(
        db,
        PermissionCreate(
            role_id=role.id,
            target_type=TargetTypeEnum.alert,
            target_id=alert.id,
            permission=PermissionEnum.read,
        ),
    )
    crud.permission.grant_permission(
        db,
        PermissionCreate(
            role_id=role2.id,
            target_type=TargetTypeEnum.alert,
            target_id=alert.id,
            permission=PermissionEnum.modify,
        ),
    )
    crud.permission.grant_permission(
        db,
        PermissionCreate(
            role_id=role2.id,
            target_type=TargetTypeEnum.alert,
            target_id=alert.id,
            permission=PermissionEnum.delete,
        ),
    )
    alert = create_random_alert(db, faker, user2)
    crud.permission.create_owner_permissions(db, user2, TargetTypeEnum.alert, alert.id)

    permissions2 = crud.permission.get_permissions(db, user2.username, TargetTypeEnum.alert, alert.id)
    assert PermissionEnum.read in permissions2
    assert PermissionEnum.modify in permissions2
    assert PermissionEnum.delete in permissions2
    assert len(permissions2) == 3
    assert PermissionEnum.read in crud.permission.get_permissions(db, user1.username, TargetTypeEnum.alert, alert.id)


def test_get_permission_roles(db: Session, faker: Faker):
    role1 = create_random_role(db, faker)
    role2 = create_random_role(db, faker)
    alert = create_random_alert(db, faker)
    permission = PermissionCreate(
        role_id=role1.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert.id,
        permission=PermissionEnum.read,
    )
    crud.permission.grant_permission(db, permission)
    permission.role_id = role2.id
    crud.permission.grant_permission(db, permission)
    permission.permission = PermissionEnum.modify
    crud.permission.grant_permission(db, permission)
    permissions = crud.permission.get_permission_roles(
        db, TargetTypeEnum.alert, alert.id
    )
    assert permissions == {
        PermissionEnum.read: [role1, role2],
        PermissionEnum.modify: [role2],
    }


def test_copy_permissions(db: Session, faker: Faker):
    role1 = create_random_role(db, faker)
    role2 = create_random_role(db, faker)
    alert1 = create_random_alert(db, faker)
    alert2 = create_random_alert(db, faker)
    permission = PermissionCreate(
        role_id=role1.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert1.id,
        permission=PermissionEnum.read,
    )
    crud.permission.grant_permission(db, permission)
    permission.role_id = role2.id
    crud.permission.grant_permission(db, permission)
    permission.permission = PermissionEnum.modify
    crud.permission.grant_permission(db, permission)
    crud.permission.copy_object_permissions(
        db,
        source_type=TargetTypeEnum.alert,
        source_id=alert1.id,
        target_type=TargetTypeEnum.alert,
        target_id=alert2.id,
    )
    permissions1 = crud.permission.get_permission_roles(
        db, TargetTypeEnum.alert, alert1.id
    )
    permissions2 = crud.permission.get_permission_roles(
        db, TargetTypeEnum.alert, alert2.id
    )
    assert permissions1 == permissions2


def test_filter_search_hits(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    alert = create_random_alert(db, faker, user)
    create_random_permission(db, [role], alert)

    db_obj = crud.permission.filter_search_hits(db, [], [role])

    assert db_obj is False

    db_obj = crud.permission.filter_search_hits(db, [{"id": alert.id, "type": TargetTypeEnum.alert}], [role])

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0].target_type == TargetTypeEnum.alert
    assert db_obj[0].target_id == alert.id
