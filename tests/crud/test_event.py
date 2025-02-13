import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum, StatusEnum
from app.models import Event
from app.schemas.event import EventCreate, EventUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.event import create_random_event
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_event(db: Session, faker: Faker) -> None:
    event = create_random_event(db, faker, create_extras=False)
    db_obj = crud.event.get(db, event.id)

    assert db_obj.id == event.id

    db_obj = crud.event.get(db, -1)

    assert db_obj is None


def test_get_multi_event(db: Session, faker: Faker) -> None:
    events = []
    for _ in range(3):
        events.append(create_random_event(db, faker, create_extras=False))

    db_objs = crud.event.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == events[0].id for i in db_objs)

    db_objs = crud.event.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == events[1].id for i in db_objs)

    db_objs = crud.event.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.event.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_event(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    event = EventCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    db_obj = crud.event.create(db, obj_in=event)

    assert db_obj.id is not None
    assert db_obj.owner == event.owner
    assert db_obj.tlp == event.tlp
    assert db_obj.status == event.status
    assert db_obj.subject == event.subject
    assert db_obj.view_count == event.view_count
    assert db_obj.message_id == event.message_id


def test_update_event(db: Session, faker: Faker) -> None:
    event = create_random_event(db, faker, create_extras=False)
    owner = create_random_user(db, faker)
    update = EventUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.event.update(db, db_obj=event, obj_in=update)

    assert db_obj.id == event.id
    assert db_obj.owner == update.owner
    assert db_obj.subject == update.subject

    update = {}

    db_obj = crud.event.update(db, db_obj=event, obj_in=update)

    assert db_obj.id == event.id

    update = {
        "test": "test"
    }

    db_obj = crud.event.update(db, db_obj=event, obj_in=update)

    assert db_obj.id == event.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "status": random.choice(list(StatusEnum)),
        "subject": faker.sentence(),
        "view_count": faker.pyint(),
        "message_id": faker.word()
    }

    db_obj = crud.event.update(db, db_obj=Event(), obj_in=update)

    assert db_obj.id == event.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.status == update["status"]
    assert db_obj.status == update["status"]
    assert db_obj.view_count == update["view_count"]
    assert db_obj.message_id == update["message_id"]


def test_remove_event(db: Session, faker: Faker) -> None:
    event = create_random_event(db, faker, create_extras=False)

    db_obj = crud.event.remove(db, _id=event.id)

    assert db_obj.id == event.id

    db_obj_del = crud.event.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.event.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_event(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    event = EventCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.event.get_or_create(db, obj_in=event)

    assert db_obj.id is not None

    same_db_obj = crud.event.get_or_create(db, obj_in=event)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_event(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    events = []
    for _ in range(3):
        events.append(create_random_event(db, faker, owner, create_extras=False))

    random_event = random.choice(events)

    db_obj, count = crud.event.query_with_filters(db, filter_dict={"id": random_event.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_event.id

    db_obj, count = crud.event.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(events)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.event.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(events) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.event.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.event.query_with_filters(db, filter_dict={"subject": random_event.subject})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_event.id

    event = create_random_event(db, faker, create_extras=False)
    promote = crud.promotion.promote(db, [{"type": TargetTypeEnum.event, "id": event.id}], TargetTypeEnum.incident)

    db_obj, count = crud.event.query_with_filters(db, filter_dict={"promoted_to": f"{TargetTypeEnum.incident.value}:{promote.id}"})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == event.id

    db_obj, count = crud.event.query_with_filters(db, filter_dict={"subject": f"!{random_event.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_event.subject for a in db_obj)


def test_get_with_roles_event(db: Session, faker: Faker) -> None:
    events = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        event = EventCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
            view_count=faker.pyint(),
            message_id=faker.word()
        )
        roles.append(role)

        events.append(crud.event.create_with_permissions(db, obj_in=event, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.event.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_event(db: Session, faker: Faker) -> None:
    events = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        event = EventCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
            view_count=faker.pyint(),
            message_id=faker.word()
        )
        roles.append(role)

        events.append(crud.event.create_with_permissions(db, obj_in=event, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.event.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_event(db: Session, faker: Faker) -> None:
    event = EventCreate(
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.event.create_with_owner(db, obj_in=event, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == event.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_event(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    event = EventCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.event.create_with_permissions(db, obj_in=event, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == event.owner
    assert db_obj.tlp == event.tlp
    assert db_obj.status == event.status
    assert db_obj.subject == event.subject
    assert db_obj.view_count == event.view_count
    assert db_obj.message_id == event.message_id

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.event, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_event(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    event = EventCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.event.create_in_object(db, obj_in=event, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == event.subject

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_event(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    event = EventCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.event.create(db, obj_in=event, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.event.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_event(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    event = create_random_event(db, faker, user, create_extras=False)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.event.remove(db, _id=event.id, audit_logger=audit_logger)

    assert db_obj.id == event.id

    db_obj = crud.event.undelete(db, db_obj.id)

    assert db_obj is None


def test_increment_view_count_event(db: Session, faker: Faker) -> None:
    event = create_random_event(db, faker, create_extras=False)
    view_count = event.view_count

    crud.event.increment_view_count(db, event.id)
    db_obj = crud.event.get(db, event.id)

    assert db_obj.id == event.id
    assert db_obj.view_count == view_count + 1
