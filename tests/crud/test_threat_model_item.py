import random
from faker import Faker
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import ThreatModelItem
from app.schemas.threat_model_item import ThreatModelItemCreate, ThreatModelItemUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.threat_model_item import create_random_threat_model_item
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker)
    db_obj = crud.threat_model_item.get(db, threat_model_item.id)

    assert db_obj.id == threat_model_item.id

    db_obj = crud.threat_model_item.get(db, -1)

    assert db_obj is None


def test_get_multi_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_items = []
    for _ in range(5):
        threat_model_items.append(create_random_threat_model_item(db, faker))

    db_objs = crud.threat_model_item.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == threat_model_items[0].id for i in db_objs)

    db_objs = crud.threat_model_item.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == threat_model_items[1].id for i in db_objs)

    db_objs = crud.threat_model_item.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.threat_model_item.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_item = ThreatModelItemCreate(
        title=faker.word(),
        type=faker.word(),
        description=faker.sentence(),
        data=jsonable_encoder(faker.pydict())
    )
    db_obj = crud.threat_model_item.create(db, obj_in=threat_model_item)

    assert db_obj.id is not None
    assert db_obj.title == threat_model_item.title
    assert db_obj.type == threat_model_item.type
    assert db_obj.description == threat_model_item.description
    assert db_obj.data == threat_model_item.data


def test_update_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker)
    update = ThreatModelItemUpdate(
        title=faker.word(),
        type=faker.word(),
        description=faker.sentence(),
        data=jsonable_encoder(faker.pydict())
    )

    db_obj = crud.threat_model_item.update(db, db_obj=threat_model_item, obj_in=update)

    assert db_obj.id == threat_model_item.id
    assert db_obj.title == update.title
    assert db_obj.type == update.type
    assert db_obj.description == update.description
    assert db_obj.data == update.data

    update = {}

    db_obj = crud.threat_model_item.update(db, db_obj=threat_model_item, obj_in=update)

    assert db_obj.id == threat_model_item.id

    update = {
        "test": "test"
    }

    db_obj = crud.threat_model_item.update(db, db_obj=threat_model_item, obj_in=update)

    assert db_obj.id == threat_model_item.id
    assert not hasattr(db_obj, "test")

    update = {
        "title": faker.word(),
        "type": faker.word(),
        "description": faker.sentence(),
        "data": jsonable_encoder(faker.pydict())
    }

    db_obj = crud.threat_model_item.update(db, db_obj=ThreatModelItem(), obj_in=update)

    assert db_obj.id == threat_model_item.id + 1
    assert db_obj.title == update["title"]
    assert db_obj.type == update["type"]
    assert db_obj.description == update["description"]
    assert db_obj.data == update["data"]


def test_remove_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker)

    db_obj = crud.threat_model_item.remove(db, _id=threat_model_item.id)

    assert db_obj.id == threat_model_item.id

    db_obj_del = crud.threat_model_item.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.threat_model_item.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_item = ThreatModelItemCreate(
        title=faker.word(),
        type=faker.word(),
        description=faker.sentence(),
        data=jsonable_encoder(faker.pydict())
    )

    db_obj = crud.threat_model_item.get_or_create(db, obj_in=threat_model_item)

    assert db_obj.id is not None

    same_db_obj = crud.threat_model_item.get_or_create(db, obj_in=threat_model_item)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_items = []
    for _ in range(5):
        threat_model_items.append(create_random_threat_model_item(db, faker))

    random_threat_model_item = random.choice(threat_model_items)

    db_obj, count = crud.threat_model_item.query_with_filters(db, filter_dict={"id": random_threat_model_item.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_threat_model_item.id

    db_obj, count = crud.threat_model_item.query_with_filters(db, filter_dict={"title": f"!{random_threat_model_item.title}"})

    assert db_obj is not None
    assert all(a.title != random_threat_model_item.title for a in db_obj)


def test_get_with_roles_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_items = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        threat_model_item = ThreatModelItemCreate(
            title=faker.word(),
            type=faker.word(),
            description=faker.sentence(),
            data=jsonable_encoder(faker.pydict())
        )
        roles.append(role)

        threat_model_items.append(crud.threat_model_item.create_with_permissions(db, obj_in=threat_model_item, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.threat_model_item.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_items = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        threat_model_item = ThreatModelItemCreate(
            title=faker.word(),
            type=faker.word(),
            description=faker.sentence(),
            data=jsonable_encoder(faker.pydict())
        )
        roles.append(role)

        threat_model_items.append(crud.threat_model_item.create_with_permissions(db, obj_in=threat_model_item, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.threat_model_item.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_item = ThreatModelItemCreate(
        title=faker.word(),
        type=faker.word(),
        description=faker.sentence(),
        data=jsonable_encoder(faker.pydict())
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.threat_model_item.create_with_owner(db, obj_in=threat_model_item, owner=owner)

    assert db_obj is not None
    assert db_obj.title == threat_model_item.title
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_threat_model_item(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    threat_model_item = ThreatModelItemCreate(
        title=faker.word(),
        type=faker.word(),
        description=faker.sentence(),
        data=jsonable_encoder(faker.pydict())
    )

    db_obj = crud.threat_model_item.create_with_permissions(db, obj_in=threat_model_item, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.title == threat_model_item.title
    assert db_obj.type == threat_model_item.type
    assert db_obj.description == threat_model_item.description
    assert db_obj.data == threat_model_item.data

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.threat_model_item, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_threat_model_item(db: Session, faker: Faker) -> None:
    threat_model_item = ThreatModelItemCreate(
        title=faker.word(),
        type=faker.word(),
        description=faker.sentence(),
        data=jsonable_encoder(faker.pydict())
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.threat_model_item.create_in_object(db, obj_in=threat_model_item, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.title == threat_model_item.title

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v0_target": TargetTypeEnum.alertgroup, "v1_id": db_obj.id, "v1_target": TargetTypeEnum.threat_model_item})

    assert count >= 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_threat_model_item(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    threat_model_item = ThreatModelItemCreate(
        title=faker.word(),
        type=faker.word(),
        description=faker.sentence(),
        data=jsonable_encoder(faker.pydict())
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.threat_model_item.create(db, obj_in=threat_model_item, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.threat_model_item.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_threat_model_item(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    threat_model_item = create_random_threat_model_item(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.threat_model_item.remove(db, _id=threat_model_item.id, audit_logger=audit_logger)

    assert db_obj.id == threat_model_item.id

    db_obj = crud.threat_model_item.undelete(db, db_obj.id)

    assert db_obj is None
