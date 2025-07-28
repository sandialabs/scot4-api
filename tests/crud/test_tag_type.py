import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import TagType
from app.schemas.tag_type import TagTypeCreate, TagTypeUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.tag_type import create_random_tag_type
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_tag_type(db: Session, faker: Faker) -> None:
    tag_type = create_random_tag_type(db, faker)
    db_obj = crud.tag_type.get(db, tag_type.id)

    assert db_obj.id == tag_type.id

    db_obj = crud.tag_type.get(db, -1)

    assert db_obj is None


def test_get_multi_tag_type(db: Session, faker: Faker) -> None:
    tag_types = []
    for _ in range(5):
        tag_types.append(create_random_tag_type(db, faker))

    db_objs = crud.tag_type.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == tag_types[0].id for i in db_objs)

    db_objs = crud.tag_type.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == tag_types[1].id for i in db_objs)

    db_objs = crud.tag_type.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.tag_type.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_tag_type(db: Session, faker: Faker) -> None:
    tag_type = TagTypeCreate(
        name=faker.word(),
        description=faker.sentence(),
    )
    db_obj = crud.tag_type.create(db, obj_in=tag_type)

    assert db_obj.id is not None
    assert db_obj.name == tag_type.name
    assert db_obj.description == tag_type.description


def test_update_tag_type(db: Session, faker: Faker) -> None:
    tag_type = create_random_tag_type(db, faker)
    update = TagTypeUpdate(
        name=faker.word(),
        description=faker.sentence(),
    )

    db_obj = crud.tag_type.update(db, db_obj=tag_type, obj_in=update)

    assert db_obj.id == tag_type.id
    assert db_obj.name == update.name
    assert db_obj.description == update.description

    update = {}

    db_obj = crud.tag_type.update(db, db_obj=tag_type, obj_in=update)

    assert db_obj.id == tag_type.id

    update = {
        "test": "test"
    }

    db_obj = crud.tag_type.update(db, db_obj=tag_type, obj_in=update)

    assert db_obj.id == tag_type.id
    assert not hasattr(db_obj, "test")

    update = {
        "name": faker.word(),
        "description": faker.sentence(),
    }

    db_obj = crud.tag_type.update(db, db_obj=TagType(), obj_in=update)

    assert db_obj.id == tag_type.id + 1
    assert db_obj.name == update["name"]
    assert db_obj.description == update["description"]


def test_remove_tag_type(db: Session, faker: Faker) -> None:
    tag_type = create_random_tag_type(db, faker)

    db_obj = crud.tag_type.remove(db, _id=tag_type.id)

    assert db_obj.id == tag_type.id

    db_obj_del = crud.tag_type.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.tag_type.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_tag_type(db: Session, faker: Faker) -> None:
    tag_type = TagTypeCreate(
        name=faker.word(),
        description=faker.sentence(),
    )

    db_obj = crud.tag_type.get_or_create(db, obj_in=tag_type)

    assert db_obj.id is not None

    same_db_obj = crud.tag_type.get_or_create(db, obj_in=tag_type)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_tag_type(db: Session, faker: Faker) -> None:
    tag_types = []
    for _ in range(5):
        tag_types.append(create_random_tag_type(db, faker))

    random_tag_type = random.choice(tag_types)

    db_obj, count = crud.tag_type.query_with_filters(db, filter_dict={"id": random_tag_type.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_tag_type.id

    db_obj, count = crud.tag_type.query_with_filters(db, filter_dict={"description": f"!{random_tag_type.description}"})

    assert db_obj is not None
    assert all(a.description != random_tag_type.description for a in db_obj)


def test_get_with_roles_tag_type(db: Session, faker: Faker) -> None:
    tag_types = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        tag_type = TagTypeCreate(
            name=faker.word(),
            description=faker.sentence(),
        )
        roles.append(role)

        tag_types.append(crud.tag_type.create_with_permissions(db, obj_in=tag_type, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.tag_type.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_tag_type(db: Session, faker: Faker) -> None:
    tag_types = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        tag_type = TagTypeCreate(
            name=faker.word(),
            description=faker.sentence(),
        )
        roles.append(role)

        tag_types.append(crud.tag_type.create_with_permissions(db, obj_in=tag_type, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.tag_type.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_tag_type(db: Session, faker: Faker) -> None:
    tag_type = TagTypeCreate(
        name=faker.word(),
        description=faker.sentence(),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.tag_type.create_with_owner(db, obj_in=tag_type, owner=owner)

    assert db_obj is not None
    assert db_obj.name == tag_type.name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_tag_type(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    tag_type = TagTypeCreate(
        name=faker.word(),
        description=faker.sentence(),
    )

    db_obj = crud.tag_type.create_with_permissions(db, obj_in=tag_type, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.name == tag_type.name
    assert db_obj.description == tag_type.description


def test_get_history_tag_type(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    tag_type = TagTypeCreate(
        name=faker.word(),
        description=faker.sentence(),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.tag_type.create(db, obj_in=tag_type, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.tag_type.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_tag_type(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    tag_type = create_random_tag_type(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.tag_type.remove(db, _id=tag_type.id, audit_logger=audit_logger)

    assert db_obj.id == tag_type.id

    db_obj = crud.tag_type.undelete(db, db_obj.id)

    assert db_obj is None
