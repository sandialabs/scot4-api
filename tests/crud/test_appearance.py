import pytest
import random
from datetime import timezone
from pydantic import ValidationError
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Appearance
from app.schemas.appearance import AppearanceCreate, AppearanceUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.appearance import create_random_appearance
from tests.utils.user import create_random_user
from tests.utils.roles import create_random_role


def test_get_appearance(db: Session, faker: Faker) -> None:
    appearance = create_random_appearance(db, faker)

    db_obj = crud.appearance.get(db, appearance.id)

    assert db_obj.id == appearance.id

    db_obj = crud.appearance.get(db, -1)

    assert db_obj is None


def test_get_multi_appearance(db: Session, faker: Faker) -> None:
    appearances = []
    for _ in range(5):
        appearances.append(create_random_appearance(db, faker))

    db_objs = crud.appearance.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == appearances[0].id for i in db_objs)

    db_objs = crud.appearance.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == appearances[1].id for i in db_objs)

    db_objs = crud.appearance.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.appearance.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_appearance(db: Session, faker: Faker) -> None:
    appearance = AppearanceCreate(
        when_date=faker.iso8601(timezone.utc),
        value_id=faker.pyint(),
        value_type=faker.word(),
        value_str=faker.sentence()
    )
    db_obj = crud.appearance.create(db, obj_in=appearance)

    assert db_obj.id is not None
    assert db_obj.when_date == appearance.when_date
    assert db_obj.value_id == appearance.value_id
    assert db_obj.value_type == appearance.value_type
    assert db_obj.value_str == appearance.value_str

    with pytest.raises(ValidationError):
        appearance = AppearanceCreate(
            value_id=faker.pyint(),
            value_type=faker.word(),
            value_str=faker.sentence()
        )
        db_obj = crud.appearance.create(db, obj_in=appearance)


def test_update_appearance(db: Session, faker: Faker) -> None:
    appearance = create_random_appearance(db, faker)
    update = AppearanceUpdate(
        when_date=faker.iso8601(timezone.utc),
        value_id=faker.pyint(),
        value_type=faker.word(),
        value_str=faker.sentence()
    )

    db_obj = crud.appearance.update(db, db_obj=appearance, obj_in=update)

    assert db_obj.id == appearance.id
    assert db_obj.when_date == update.when_date

    update = {
        "value_id": faker.pyint(),
        "value_type": faker.word(),
        "value_str": faker.sentence()
    }

    db_obj = crud.appearance.update(db, db_obj=appearance, obj_in=update)

    assert db_obj.value_id == update["value_id"]
    assert db_obj.value_type == update["value_type"]
    assert db_obj.value_str == update["value_str"]

    update = {}

    db_obj = crud.appearance.update(db, db_obj=appearance, obj_in=update)

    assert db_obj.id == appearance.id

    update = {
        "test": "test"
    }

    db_obj = crud.appearance.update(db, db_obj=appearance, obj_in=update)

    assert db_obj.id == appearance.id
    assert not hasattr(db_obj, "test")

    update = {
        "value_id": faker.pyint(),
        "value_type": faker.word(),
        "value_str": faker.sentence()
    }

    db_obj = crud.appearance.update(db, db_obj=Appearance(), obj_in=update)

    assert db_obj.id == appearance.id + 1
    assert db_obj.value_id == update["value_id"]
    assert db_obj.value_type == update["value_type"]


def test_remove_appearance(db: Session, faker: Faker) -> None:
    appearance = create_random_appearance(db, faker)

    db_obj = crud.appearance.remove(db, _id=appearance.id)

    assert db_obj.id == appearance.id

    db_obj_del = crud.appearance.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.appearance.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_appearance(db: Session, faker: Faker) -> None:
    appearance = {
        "value_id": faker.pyint(),
        "value_type": faker.word(),
        "value_str": faker.sentence()
    }

    db_obj = crud.appearance.get_or_create(db, obj_in=appearance)

    assert db_obj.id is not None

    same_db_obj = crud.appearance.get_or_create(db, obj_in=appearance)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_appearance(db: Session, faker: Faker) -> None:
    appearances = []
    for _ in range(5):
        appearances.append(create_random_appearance(db, faker))

    random_appearance = random.choice(appearances)

    db_obj, count = crud.appearance.query_with_filters(db, filter_dict={"id": random_appearance.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_appearance.id

    db_obj, count = crud.appearance.query_with_filters(db, filter_dict={"value_id": random_appearance.value_id})

    assert db_obj is not None
    assert len(db_obj) == count
    assert all(a.value_id == random_appearance.value_id for a in db_obj)

    db_obj, count = crud.appearance.query_with_filters(db, filter_dict={"value_id": random_appearance.value_id}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == count - 1
    assert all(a.value_id == random_appearance.value_id for a in db_obj)

    db_obj, count = crud.appearance.query_with_filters(db, filter_dict={"value_id": random_appearance.value_id}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.value_id == random_appearance.value_id for a in db_obj)

    db_obj, count = crud.appearance.query_with_filters(db, filter_dict={"value_str": f"!{random_appearance.value_str}"})

    assert db_obj is not None
    assert all(a.value_str != random_appearance.value_str for a in db_obj)


def test_get_with_roles_appearance(db: Session, faker: Faker) -> None:
    appearances = []
    roles = []
    for _ in range(5):
        appearance = AppearanceCreate(
            when_date=faker.iso8601(timezone.utc),
            value_id=faker.pyint(),
            value_type=faker.word(),
            value_str=faker.sentence()
        )
        role = create_random_role(db, faker)
        roles.append(role)

        appearances.append(crud.appearance.create_with_permissions(db, obj_in=appearance, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.appearance.get_with_roles(db, [random_role])

    assert db_obj == []


def test_query_objects_with_roles_appearance(db: Session, faker: Faker) -> None:
    appearances = []
    roles = []
    for _ in range(5):
        appearance = AppearanceCreate(
            when_date=faker.iso8601(timezone.utc),
            value_id=faker.pyint(),
            value_type=faker.word(),
            value_str=faker.sentence()
        )
        role = create_random_role(db, faker)
        roles.append(role)

        appearances.append(crud.appearance.create_with_permissions(db, obj_in=appearance, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.appearance.get_with_roles(db, [random_role])

    assert db_obj == []


def test_create_with_owner_appearance(db: Session, faker: Faker) -> None:
    appearance = AppearanceCreate(
        when_date=faker.iso8601(timezone.utc),
        value_id=faker.pyint(),
        value_type=faker.word(),
        value_str=faker.sentence()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.appearance.create_with_owner(db, obj_in=appearance, owner=owner)

    assert db_obj is not None
    assert db_obj.when_date == appearance.when_date
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_appearance(db: Session, faker: Faker) -> None:
    appearance = AppearanceCreate(
        when_date=faker.iso8601(timezone.utc),
        value_id=faker.pyint(),
        value_type=faker.word(),
        value_str=faker.sentence()
    )
    role = create_random_role(db, faker)

    db_obj = crud.appearance.create_with_permissions(db, obj_in=appearance, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.when_date == appearance.when_date
    assert db_obj.value_id == appearance.value_id
    assert db_obj.value_type == appearance.value_type
    assert db_obj.value_str == appearance.value_str


def test_create_in_object_appearance(db: Session, faker: Faker) -> None:
    appearance = AppearanceCreate(
        when_date=faker.iso8601(timezone.utc),
        value_id=faker.pyint(),
        value_type=faker.word(),
        value_str=faker.sentence()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.appearance.create_in_object(db, obj_in=appearance, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.when_date == appearance.when_date

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 0
    assert len(link) == 0


def test_get_history_appearance(db: Session, faker: Faker) -> None:
    appearance = AppearanceCreate(
        when_date=faker.iso8601(timezone.utc),
        value_id=faker.pyint(),
        value_type=faker.word(),
        value_str=faker.sentence()
    )
    user = create_random_user(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.appearance.create(db, obj_in=appearance, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.appearance.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_appearance(db: Session, faker: Faker) -> None:
    appearance = create_random_appearance(db, faker)
    user = create_random_user(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.appearance.remove(db, _id=appearance.id, audit_logger=audit_logger)

    assert db_obj.id == appearance.id

    db_obj = crud.appearance.undelete(db, db_obj.id)

    assert db_obj is None
