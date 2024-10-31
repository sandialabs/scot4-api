import pytest
import random
from pydantic import ValidationError
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.schemas.audit import AuditCreate, AuditUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.audit import create_audit
from tests.utils.user import create_random_user
from tests.utils.roles import create_random_role


def test_get_audit(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert_group = create_random_alertgroup_no_sig(db, faker, user.username, False)
    audit = create_audit(db, faker, user.username, alert_group, TargetTypeEnum.alertgroup)

    db_obj = crud.audit.get(db, audit.id)

    assert db_obj.id == audit.id

    db_obj = crud.audit.get(db, -1)

    assert db_obj is None


def test_get_multi_audit(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert_group = create_random_alertgroup_no_sig(db, faker, user.username, False)
    audits = []
    for _ in range(5):
        audits.append(create_audit(db, faker, user.username, alert_group, TargetTypeEnum.alertgroup))

    db_objs = crud.audit.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == audits[0].id for i in db_objs)

    db_objs = crud.audit.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == audits[1].id for i in db_objs)

    db_objs = crud.audit.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.audit.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_audit(db: Session, faker: Faker) -> None:
    audit = AuditCreate(
        what="create",
        when_date=faker.iso8601(),
        thing_id=faker.pyint(),
        thing_type=faker.word(),
    )
    db_obj = crud.audit.create(db, obj_in=audit)

    assert db_obj.id is not None
    assert db_obj.thing_id == audit.thing_id
    assert db_obj.thing_type == audit.thing_type

    with pytest.raises(ValidationError):
        audit = AuditCreate(
            thing_id=faker.pyint(),
            thing_type=faker.word(),
        )
        db_obj = crud.audit.create(db, obj_in=audit)


def test_update_audit(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert_group = create_random_alertgroup_no_sig(db, faker, user.username, False)
    audit = create_audit(db, faker, user.username, alert_group, TargetTypeEnum.alertgroup)

    update = AuditUpdate(
        when_date=faker.iso8601(),
        thing_id=faker.pyint(),
        thing_type=faker.word(),
    )

    db_obj = crud.audit.update(db, db_obj=audit, obj_in=update)

    assert db_obj.id == audit.id
    assert db_obj.thing_id == update.thing_id

    update = {
        "thing_id": faker.pyint(),
        "thing_type": faker.word(),
    }

    db_obj = crud.audit.update(db, db_obj=audit, obj_in=update)

    assert db_obj.thing_id == update["thing_id"]
    assert db_obj.thing_type == update["thing_type"]

    update = {}

    db_obj = crud.audit.update(db, db_obj=audit, obj_in=update)

    assert db_obj.id == audit.id

    update = {
        "test": "test"
    }

    db_obj = crud.audit.update(db, db_obj=audit, obj_in=update)

    assert db_obj.id == audit.id
    assert not hasattr(db_obj, "test")

    update = {
        "thing_id": faker.pyint(),
        "thing_type": faker.word(),
    }

    db_obj = crud.audit.update(db, db_obj=audit, obj_in=update)

    assert db_obj.id == audit.id
    assert db_obj.thing_id == update["thing_id"]
    assert db_obj.thing_type == update["thing_type"]


def test_remove_audit(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert_group = create_random_alertgroup_no_sig(db, faker, user.username, False)
    audit = create_audit(db, faker, user.username, alert_group, TargetTypeEnum.alertgroup)
    db_obj = crud.audit.remove(db, _id=audit.id)

    assert db_obj.id == audit.id

    db_obj_del = crud.audit.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.audit.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_audit(db: Session, faker: Faker) -> None:
    audit = {
        "what": "create",
        "thing_id": faker.pyint(),
        "thing_type": faker.word(),
    }

    db_obj = crud.audit.get_or_create(db, obj_in=audit)

    assert db_obj.id is not None

    same_db_obj = crud.audit.get_or_create(db, obj_in=audit)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_audit(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert_group = create_random_alertgroup_no_sig(db, faker, user.username, False)
    audits = []
    for _ in range(5):
        audits.append(create_audit(db, faker, user.username, alert_group, TargetTypeEnum.alertgroup))

    random_audit = random.choice(audits)

    db_obj, count = crud.audit.query_with_filters(db, filter_dict={"id": random_audit.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_audit.id

    db_obj, count = crud.audit.query_with_filters(db, filter_dict={"thing_id": random_audit.thing_id})

    assert db_obj is not None
    assert len(db_obj) == count
    assert all(a.thing_id == random_audit.thing_id for a in db_obj)

    db_obj, count = crud.audit.query_with_filters(db, filter_dict={"thing_id": random_audit.thing_id}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == count - 1
    assert all(a.thing_id == random_audit.thing_id for a in db_obj)

    db_obj, count = crud.audit.query_with_filters(db, filter_dict={"thing_id": random_audit.thing_id}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.thing_id == random_audit.thing_id for a in db_obj)

    db_obj, count = crud.audit.query_with_filters(db, filter_dict={"what": f"!{random_audit.what}"})

    assert db_obj is not None
    assert all(a.what != random_audit.what for a in db_obj)


def test_get_with_roles_audit(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    audits = []
    roles = []
    for _ in range(5):
        audit = AuditCreate(
            what="create",
            when_date=faker.iso8601(),
            username=user.username,
            thing_id=faker.pyint(),
            thing_type=faker.word(),
        )
        role = create_random_role(db, faker)
        roles.append(role)

        audits.append(crud.audit.create_with_permissions(db, obj_in=audit, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.audit.get_with_roles(db, [random_role])

    assert db_obj == []


def test_query_objects_with_roles_audit(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    audits = []
    roles = []
    for _ in range(5):
        audit = AuditCreate(
            what="create",
            when_date=faker.iso8601(),
            username=user.username,
            thing_id=faker.pyint(),
            thing_type=faker.word(),
        )
        role = create_random_role(db, faker)
        roles.append(role)

        audits.append(crud.audit.create_with_permissions(db, obj_in=audit, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.audit.get_with_roles(db, [random_role])

    assert db_obj == []


def test_create_with_owner_audit(db: Session, faker: Faker) -> None:
    audit = AuditCreate(
        what="create",
        when_date=faker.iso8601(),
        thing_id=faker.pyint(),
        thing_type=faker.word(),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.audit.create_with_owner(db, obj_in=audit, owner=owner)

    assert db_obj is not None
    assert db_obj.thing_id == audit.thing_id
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_audit(db: Session, faker: Faker) -> None:
    audit = AuditCreate(
        what="create",
        when_date=faker.iso8601(),
        thing_id=faker.pyint(),
        thing_type=faker.word(),
    )
    role = create_random_role(db, faker)

    db_obj = crud.audit.create_with_permissions(db, obj_in=audit, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.thing_id == audit.thing_id
    assert db_obj.thing_type == audit.thing_type

    # no permission could be created with audits so nothing should be returned
    db_obj, count = crud.permission.query_with_filters(db, filter_dict={"target_id": db_obj.id})

    assert db_obj == []
    assert count == 0


def test_create_in_object_audit(db: Session, faker: Faker) -> None:
    audit = AuditCreate(
        what="create",
        when_date=faker.iso8601(),
        thing_id=faker.pyint(),
        thing_type=faker.word(),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.audit.create_in_object(db, obj_in=audit, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.thing_id == audit.thing_id

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 0
    assert len(link) == 0


def test_get_history_audit(db: Session, faker: Faker) -> None:
    audit = AuditCreate(
        what="create",
        when_date=faker.iso8601(),
        thing_id=faker.pyint(),
        thing_type=faker.word(),
    )
    user = create_random_user(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.audit.create(db, obj_in=audit, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.audit.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_audit(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert_group = create_random_alertgroup_no_sig(db, faker, user.username, False)
    audit = create_audit(db, faker, user.username, alert_group, TargetTypeEnum.alertgroup)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.audit.remove(db, _id=audit.id, audit_logger=audit_logger)

    assert db_obj.id == audit.id

    db_obj = crud.audit.undelete(db, db_obj.id)

    assert db_obj is None
