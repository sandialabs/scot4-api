import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Role
from app.schemas.role import RoleCreate, RoleUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_role(db: Session, faker: Faker) -> None:
    role_orig = create_random_role(db, faker)
    role = crud.role.get(db, role_orig.id)

    assert role.id == role_orig.id

    role = crud.role.get(db, -1)

    assert role is None


def test_get_multi_role(db: Session, faker: Faker) -> None:
    roles = []
    for _ in range(5):
        roles.append(create_random_role(db, faker))

    db_objs = crud.role.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == roles[0].id for i in db_objs)

    db_objs = crud.role.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == roles[1].id for i in db_objs)

    db_objs = crud.role.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.role.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_role(db: Session, faker: Faker) -> None:
    role_create = RoleCreate(
        name=f"{faker.unique.word()}_{faker.pyint()}",
        description=faker.sentence(12)
    )

    role = crud.role.create(db, obj_in=role_create)

    assert role is not None
    assert role.name == role_create.name
    assert role.description == role_create.description


def test_update_role(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    role_update = RoleUpdate(
        name=f"{faker.unique.word()}_{faker.pyint()}",
        description=faker.sentence(12)
    )
    new_role = crud.role.update(db, db_obj=role, obj_in=role_update)

    assert new_role.id == role.id
    assert new_role.name == role_update.name
    assert new_role.description == role_update.description

    update = {}

    db_obj = crud.role.update(db, db_obj=role, obj_in=update)

    assert db_obj.id == role.id

    update = {
        "test": "test"
    }

    db_obj = crud.role.update(db, db_obj=role, obj_in=update)

    assert db_obj.id == role.id
    assert not hasattr(db_obj, "test")

    update = {
        "name": f"{faker.unique.word()}_{faker.pyint()}",
        "description": faker.sentence(12)
    }

    db_obj = crud.role.update(db, db_obj=Role(), obj_in=update)

    assert db_obj.id == role.id + 1
    assert db_obj.name == update["name"]
    assert db_obj.description == update["description"]


def test_remove_role(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)

    db_obj = crud.role.remove(db, _id=role.id)

    assert db_obj.id == role.id

    role_get_delete = crud.role.get(db, role.id)

    assert role_get_delete is None

    db_obj = crud.role.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_role(db: Session, faker: Faker) -> None:
    role = RoleCreate(
        name=f"{faker.unique.word()}_{faker.pyint()}",
        description=faker.sentence(12)
    )

    db_obj = crud.role.get_or_create(db, obj_in=role)

    assert db_obj.id is not None

    same_db_obj = crud.role.get_or_create(db, obj_in=role)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_role(db: Session, faker: Faker) -> None:
    roles = []
    for _ in range(5):
        roles.append(create_random_role(db, faker))

    random_role = random.choice(roles)

    db_obj, count = crud.role.query_with_filters(db, filter_dict={"id": random_role.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_role.id

    db_obj, count = crud.role.query_with_filters(db, filter_dict={"description": f"!{random_role.description}"})

    assert db_obj is not None
    assert all(a.description != random_role.description for a in db_obj)


def test_get_with_roles_role(db: Session, faker: Faker) -> None:
    roles1 = []
    roles = []
    for _ in range(5):
        role1 = create_random_role(db, faker)
        role = RoleCreate(
            name=f"{faker.unique.word()}_{faker.pyint()}",
            description=faker.sentence(12)
        )
        roles1.append(role1)

        roles.append(crud.role.create_with_permissions(db, obj_in=role, perm_in={PermissionEnum.read: [role1.id]}))

    random_role = random.choice(roles1)
    db_obj = crud.role.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_role(db: Session, faker: Faker) -> None:
    roles1 = []
    roles = []
    for _ in range(5):
        role1 = create_random_role(db, faker)
        role = RoleCreate(
            name=f"{faker.unique.word()}_{faker.pyint()}",
            description=faker.sentence(12)
        )
        roles1.append(role1)

        roles.append(crud.role.create_with_permissions(db, obj_in=role, perm_in={PermissionEnum.read: [role1.id]}))

    random_role = random.choice(roles1)
    db_obj = crud.role.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_role(db: Session, faker: Faker) -> None:
    role = RoleCreate(
        name=f"{faker.unique.word()}_{faker.pyint()}",
        description=faker.sentence(12)
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.role.create_with_owner(db, obj_in=role, owner=owner)

    assert db_obj is not None
    assert db_obj.name == role.name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_role(db: Session, faker: Faker) -> None:
    role1 = create_random_role(db, faker)
    role = RoleCreate(
        name=f"{faker.unique.word()}_{faker.pyint()}",
        description=faker.sentence(12)
    )

    db_obj = crud.role.create_with_permissions(db, obj_in=role, perm_in={PermissionEnum.read: [role1.id]})

    assert db_obj.id is not None
    assert db_obj.name == role.name
    assert db_obj.description == role.description


def test_create_in_object_role(db: Session, faker: Faker) -> None:
    role = RoleCreate(
        name=f"{faker.unique.word()}_{faker.pyint()}",
        description=faker.sentence(12)
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.role.create_in_object(db, obj_in=role, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.name == role.name

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v0_target": TargetTypeEnum.alertgroup, "v1_id": db_obj.id})

    assert count == 0
    assert len(link) == 0


def test_get_history_role(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    role = RoleCreate(
        name=f"{faker.unique.word()}_{faker.pyint()}",
        description=faker.sentence(12)
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.role.create(db, obj_in=role, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.role.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_role(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    role = create_random_role(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.role.remove(db, _id=role.id, audit_logger=audit_logger)

    assert db_obj.id == role.id

    db_obj = crud.role.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_role_by_name(db: Session, faker: Faker) -> None:
    role_orig = create_random_role(db, faker)

    role = crud.role.get_role_by_name(db, role_orig.name)

    assert role.id == role_orig.id

    role = crud.role.get_role_by_name(db, "")

    assert role is None


def test_get_role_by_name(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    new_role_names = [faker.unique.word(), faker.unique.word()]
    crud.role.ensure_roles_on_user(db, user, role_names=new_role_names, create=True)

    assert len(user.roles) == 2
    assert set([r.name for r in user.roles]) == set(new_role_names)

    # Test adding roles to user at creation
    user2 = create_random_user(db, faker, roles=new_role_names)

    assert len(user2.roles) == 2
    assert set([r.name for r in user2.roles]) == set(new_role_names)
