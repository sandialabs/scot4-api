import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import EntityClass
from app.schemas.entity_class import EntityClassCreate, EntityClassUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.entity_class import create_random_entity_class
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user
from tests.utils.entity import create_random_entity


def test_get_entity_class(db: Session, faker: Faker) -> None:
    entity_class = create_random_entity_class(db, faker)
    db_obj = crud.entity_class.get(db, entity_class.id)

    assert db_obj.id == entity_class.id

    db_obj = crud.entity_class.get(db, -1)

    assert db_obj is None


def test_get_multi_entity_class(db: Session, faker: Faker) -> None:
    entity_classes = []
    for _ in range(5):
        entity_classes.append(create_random_entity_class(db, faker))

    db_objs = crud.entity_class.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == entity_classes[0].id for i in db_objs)

    db_objs = crud.entity_class.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == entity_classes[1].id for i in db_objs)

    db_objs = crud.entity_class.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.entity_class.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_entity_class(db: Session, faker: Faker) -> None:
    entity_class = EntityClassCreate(
        display_name=faker.sentence(),
        name=f"{faker.word()}_{faker.pyint()}",
    )
    db_obj = crud.entity_class.create(db, obj_in=entity_class)

    assert db_obj.id is not None
    assert db_obj.display_name == entity_class.display_name
    assert db_obj.name == entity_class.name


def test_update_entity_class(db: Session, faker: Faker) -> None:
    entity_class = create_random_entity_class(db, faker)
    update = EntityClassUpdate(
        display_name=faker.sentence(),
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence()
    )

    db_obj = crud.entity_class.update(db, db_obj=entity_class, obj_in=update)

    assert db_obj.id == entity_class.id
    assert db_obj.display_name == update.display_name
    assert db_obj.name == update.name
    assert db_obj.description == update.description

    update = {}

    db_obj = crud.entity_class.update(db, db_obj=entity_class, obj_in=update)

    assert db_obj.id == entity_class.id

    update = {
        "test": "test"
    }

    db_obj = crud.entity_class.update(db, db_obj=entity_class, obj_in=update)

    assert db_obj.id == entity_class.id
    assert not hasattr(db_obj, "test")

    update = {
        "display_name": faker.sentence(),
        "name": faker.word(),
        "description": faker.sentence()
    }

    db_obj = crud.entity_class.update(db, db_obj=EntityClass(), obj_in=update)

    assert db_obj.display_name == update["display_name"]
    assert db_obj.name == update["name"]
    assert db_obj.description == update["description"]


def test_remove_entity_class(db: Session, faker: Faker) -> None:
    entity_class = create_random_entity_class(db, faker)

    db_obj = crud.entity_class.remove(db, _id=entity_class.id)

    assert db_obj.id == entity_class.id

    db_obj_del = crud.entity_class.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.entity_class.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_entity_class(db: Session, faker: Faker) -> None:
    entity_class = EntityClassCreate(
        display_name=faker.sentence(),
        name=f"{faker.word()}_{faker.pyint()}",
    )

    db_obj = crud.entity_class.get_or_create(db, obj_in=entity_class)

    assert db_obj.id is not None

    same_db_obj = crud.entity_class.get_or_create(db, obj_in=entity_class)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_entity_class(db: Session, faker: Faker) -> None:
    entity_classes = []
    for _ in range(5):
        entity_classes.append(create_random_entity_class(db, faker))

    random_entity_class = random.choice(entity_classes)

    db_obj, count = crud.entity_class.query_with_filters(db, filter_dict={"id": random_entity_class.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_entity_class.id

    db_obj, count = crud.entity_class.query_with_filters(db, filter_dict={"name": f"!{random_entity_class.name}"})

    assert db_obj is not None
    assert all(a.name != random_entity_class.name for a in db_obj)


def test_get_with_roles_entity_class(db: Session, faker: Faker) -> None:
    entity_classes = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        entity_class = EntityClassCreate(
            display_name=faker.sentence(),
            name=f"{faker.word()}_{faker.pyint()}",
        )
        roles.append(role)

        entity_classes.append(crud.entity_class.create_with_permissions(db, obj_in=entity_class, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.entity_class.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_entity_class(db: Session, faker: Faker) -> None:
    entity_classes = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        entity_class = EntityClassCreate(
            display_name=faker.sentence(),
            name=f"{faker.word()}_{faker.pyint()}",
        )
        roles.append(role)

        entity_classes.append(crud.entity_class.create_with_permissions(db, obj_in=entity_class, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.entity_class.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_entity_class(db: Session, faker: Faker) -> None:
    entity_class = EntityClassCreate(
        display_name=faker.sentence(),
        name=f"{faker.word()}_{faker.pyint()}",
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.entity_class.create_with_owner(db, obj_in=entity_class, owner=owner)

    assert db_obj is not None
    assert db_obj.display_name == entity_class.display_name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_entity_class(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    entity_class = EntityClassCreate(
        display_name=faker.sentence(),
        name=f"{faker.word()}_{faker.pyint()}",
    )

    db_obj = crud.entity_class.create_with_permissions(db, obj_in=entity_class, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.display_name == entity_class.display_name
    assert db_obj.name == entity_class.name

    # no permission could be created with appearances so nothing should be returned
    db_query, count = crud.permission.query_with_filters(db, filter_dict={"target_id": db_obj.id, "role_id": role.id})

    assert len(db_query) == 1
    assert count == 1
    assert db_query[0].target_id == db_obj.id
    assert db_query[0].role_id == role.id


def test_create_in_object_entity_class(db: Session, faker: Faker) -> None:
    entity_class = EntityClassCreate(
        display_name=faker.sentence(),
        name=f"{faker.word()}_{faker.pyint()}",
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.entity_class.create_in_object(db, obj_in=entity_class, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.display_name == entity_class.display_name

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_entity_class(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entity_class = EntityClassCreate(
        display_name=faker.sentence(),
        name=f"{faker.word()}_{faker.pyint()}",
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.entity_class.create(db, obj_in=entity_class, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.entity_class.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_entity_class(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entity_class = create_random_entity_class(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.entity_class.remove(db, _id=entity_class.id, audit_logger=audit_logger)

    assert db_obj.id == entity_class.id

    db_obj = crud.entity_class.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_by_name_entity_class(db: Session, faker: Faker) -> None:
    entity_class = create_random_entity_class(db, faker)

    entity_class_get = crud.entity_class.get_by_name(db, entity_class.name)

    assert entity_class.id == entity_class_get.id

    entity_class_get = crud.entity_class.get_by_name(db, "test")

    assert entity_class_get is None
