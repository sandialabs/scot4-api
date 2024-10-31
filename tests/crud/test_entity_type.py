import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum, EntityTypeStatusEnum
from app.models import EntityType
from app.schemas.entity_type import EntityTypeCreate, EntityTypeUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.entity_type import create_random_entity_type
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_entity_type(db: Session, faker: Faker) -> None:
    entity_type = create_random_entity_type(db, faker)
    db_obj = crud.entity_type.get(db, entity_type.id)

    assert db_obj.id == entity_type.id

    db_obj = crud.entity_type.get(db, -1)

    assert db_obj is None


def test_get_multi_entity_type(db: Session, faker: Faker) -> None:
    entity_types = []
    for _ in range(5):
        entity_types.append(create_random_entity_type(db, faker))

    db_objs = crud.entity_type.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == entity_types[0].id for i in db_objs)

    db_objs = crud.entity_type.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == entity_types[1].id for i in db_objs)

    db_objs = crud.entity_type.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.entity_type.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_entity_type(db: Session, faker: Faker) -> None:
    entity_type = EntityTypeCreate(
        name=faker.sentence(),
        match_order=faker.pyint(),
        status=random.choice(list(EntityTypeStatusEnum)),
        match=faker.word(),
        entity_type_data_ver=str(faker.pyfloat(1, 1, True))
    )
    db_obj = crud.entity_type.create(db, obj_in=entity_type)

    assert db_obj.id is not None
    assert db_obj.name == entity_type.name
    assert db_obj.match_order == entity_type.match_order
    assert db_obj.status == entity_type.status
    assert db_obj.match == entity_type.match
    assert db_obj.entity_type_data_ver == entity_type.entity_type_data_ver


def test_update_entity_type(db: Session, faker: Faker) -> None:
    entity_type = create_random_entity_type(db, faker)
    update = EntityTypeUpdate(
        name=faker.sentence(),
        match_order=faker.pyint(),
    )

    db_obj = crud.entity_type.update(db, db_obj=entity_type, obj_in=update)

    assert db_obj.id == entity_type.id
    assert db_obj.name == update.name
    assert db_obj.match_order == update.match_order

    update = {}

    db_obj = crud.entity_type.update(db, db_obj=entity_type, obj_in=update)

    assert db_obj.id == entity_type.id

    update = {
        "test": "test"
    }

    db_obj = crud.entity_type.update(db, db_obj=entity_type, obj_in=update)

    assert db_obj.id == entity_type.id
    assert not hasattr(db_obj, "test")

    update = {
        "name": faker.sentence(),
        "match_order": faker.pyint(),
    }

    db_obj = crud.entity_type.update(db, db_obj=EntityType(), obj_in=update)

    assert db_obj.id == entity_type.id + 1
    assert db_obj.name == update["name"]
    assert db_obj.match_order == update["match_order"]


def test_remove_entity_type(db: Session, faker: Faker) -> None:
    entity_type = create_random_entity_type(db, faker)

    db_obj = crud.entity_type.remove(db, _id=entity_type.id)

    assert db_obj.id == entity_type.id

    db_obj_del = crud.entity_type.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.entity_type.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_entity_type(db: Session, faker: Faker) -> None:
    entity_type = EntityTypeCreate(
        name=faker.sentence(),
        match_order=faker.pyint(),
        status=random.choice(list(EntityTypeStatusEnum)),
        match=faker.word(),
        entity_type_data_ver=str(faker.pyfloat(1, 1, True)),
    )

    db_obj = crud.entity_type.get_or_create(db, obj_in=entity_type)

    assert db_obj.id is not None

    same_db_obj = crud.entity_type.get_or_create(db, obj_in=entity_type)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_entity_type(db: Session, faker: Faker) -> None:
    entity_types = []
    for _ in range(5):
        entity_types.append(create_random_entity_type(db, faker))

    random_entity_type = random.choice(entity_types)

    db_obj, count = crud.entity_type.query_with_filters(db, filter_dict={"id": random_entity_type.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_entity_type.id

    db_obj, count = crud.entity_type.query_with_filters(db, filter_dict={"name": f"!{random_entity_type.name}"})

    assert db_obj is not None
    assert all(a.name != random_entity_type.name for a in db_obj)


def test_get_with_roles_entity_type(db: Session, faker: Faker) -> None:
    entity_types = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        entity_type = EntityTypeCreate(
            name=faker.sentence(),
            match_order=faker.pyint(),
            status=random.choice(list(EntityTypeStatusEnum)),
            match=faker.word(),
            entity_type_data_ver=str(faker.pyfloat(1, 1, True)),
        )
        roles.append(role)

        entity_types.append(crud.entity_type.create_with_permissions(db, obj_in=entity_type, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.entity_type.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_entity_type(db: Session, faker: Faker) -> None:
    entity_types = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        entity_type = EntityTypeCreate(
            name=faker.sentence(),
            match_order=faker.pyint(),
            status=random.choice(list(EntityTypeStatusEnum)),
            match=faker.word(),
            entity_type_data_ver=str(faker.pyfloat(1, 1, True)),
        )
        roles.append(role)

        entity_types.append(crud.entity_type.create_with_permissions(db, obj_in=entity_type, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.entity_type.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_entity_type(db: Session, faker: Faker) -> None:
    entity_type = EntityTypeCreate(
        name=faker.sentence(),
        match_order=faker.pyint(),
        status=random.choice(list(EntityTypeStatusEnum)),
        match=faker.word(),
        entity_type_data_ver=str(faker.pyfloat(1, 1, True)),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.entity_type.create_with_owner(db, obj_in=entity_type, owner=owner)

    assert db_obj is not None
    assert db_obj.name == entity_type.name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_entity_type(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    entity_type = EntityTypeCreate(
        name=faker.sentence(),
        match_order=faker.pyint(),
        status=random.choice(list(EntityTypeStatusEnum)),
        match=faker.word(),
        entity_type_data_ver=str(faker.pyfloat(1, 1, True)),
    )

    db_obj = crud.entity_type.create_with_permissions(db, obj_in=entity_type, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.name == entity_type.name
    assert db_obj.match_order == entity_type.match_order
    assert db_obj.status == entity_type.status
    assert db_obj.match == entity_type.match
    assert db_obj.entity_type_data_ver == entity_type.entity_type_data_ver
    assert db_obj.entity_type_data == entity_type.entity_type_data

    # no permission could be created with appearances so nothing should be returned
    query_obj, count = crud.permission.query_with_filters(db, filter_dict={"target_id": db_obj.id, "role_id": role.id})

    assert len(query_obj) == 1
    assert count == 1
    assert query_obj[0].target_id == db_obj.id
    assert query_obj[0].role_id == role.id


def test_create_in_object_entity_type(db: Session, faker: Faker) -> None:
    entity_type = EntityTypeCreate(
        name=faker.sentence(),
        match_order=faker.pyint(),
        status=random.choice(list(EntityTypeStatusEnum)),
        match=faker.word(),
        entity_type_data_ver=str(faker.pyfloat(1, 1, True)),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.entity_type.create_in_object(db, obj_in=entity_type, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.name == entity_type.name

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_entity_type(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entity_type = EntityTypeCreate(
        name=faker.sentence(),
        match_order=faker.pyint(),
        status=random.choice(list(EntityTypeStatusEnum)),
        match=faker.word(),
        entity_type_data_ver=str(faker.pyfloat(1, 1, True)),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.entity_type.create(db, obj_in=entity_type, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.entity_type.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_entity_type(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entity_type = create_random_entity_type(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.entity_type.remove(db, _id=entity_type.id, audit_logger=audit_logger)

    assert db_obj.id == entity_type.id

    db_obj = crud.entity_type.undelete(db, db_obj.id)

    assert db_obj is None
