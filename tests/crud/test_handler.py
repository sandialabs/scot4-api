import random
from datetime import timedelta
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Handler
from app.schemas.handler import HandlerCreate, HandlerUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.handler import create_random_handler
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_handler(db: Session, faker: Faker) -> None:
    handler = create_random_handler(db, faker)
    db_obj = crud.handler.get(db, handler.id)

    assert db_obj.id == handler.id

    db_obj = crud.handler.get(db, -1)

    assert db_obj is None


def test_get_multi_handler(db: Session, faker: Faker) -> None:
    handlers = []
    for _ in range(5):
        handlers.append(create_random_handler(db, faker))

    db_objs = crud.handler.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == handlers[0].id for i in db_objs)

    db_objs = crud.handler.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == handlers[1].id for i in db_objs)

    db_objs = crud.handler.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.handler.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_handler(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    start_date = faker.date_time_this_month()
    handler = HandlerCreate(
        start_date=start_date,
        end_date=start_date + timedelta(days=7),
        username=owner.username,
        position=faker.word()
    )
    db_obj = crud.handler.create(db, obj_in=handler)

    assert db_obj.id is not None
    assert db_obj.start_date.replace(tzinfo=None) == handler.start_date
    assert db_obj.end_date.replace(tzinfo=None) == handler.end_date
    assert db_obj.username == handler.username
    assert db_obj.position == handler.position


def test_update_handler(db: Session, faker: Faker) -> None:
    handler = create_random_handler(db, faker)
    owner = create_random_user(db, faker)
    start_date = faker.date_time_this_month()
    update = HandlerUpdate(
        start_date=start_date,
        end_date=start_date + timedelta(days=7),
        username=owner.username,
        position=faker.word()
    )
    db_obj = crud.handler.update(db, db_obj=handler, obj_in=update)

    assert db_obj.id == handler.id
    assert db_obj.start_date.replace(tzinfo=None) == update.start_date
    assert db_obj.username == update.username
    assert db_obj.end_date.replace(tzinfo=None) == update.end_date
    assert db_obj.position == update.position

    update = {}

    db_obj = crud.handler.update(db, db_obj=handler, obj_in=update)

    assert db_obj.id == handler.id

    update = {
        "test": "test"
    }

    db_obj = crud.handler.update(db, db_obj=handler, obj_in=update)

    assert db_obj.id == handler.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    start_date = faker.date_time_this_month()
    update = {
        "start_date": start_date,
        "end_date": start_date + timedelta(days=7),
        "username": owner.username,
        "position": faker.word()
    }

    db_obj = crud.handler.update(db, db_obj=Handler(), obj_in=update)

    assert db_obj.id == handler.id + 1
    assert db_obj.start_date.replace(tzinfo=None) == update["start_date"]
    assert db_obj.end_date.replace(tzinfo=None) == update["end_date"]
    assert db_obj.username == update["username"]
    assert db_obj.position == update["position"]


def test_remove_handler(db: Session, faker: Faker) -> None:
    handler = create_random_handler(db, faker)

    db_obj = crud.handler.remove(db, _id=handler.id)

    assert db_obj.id == handler.id

    db_obj_del = crud.handler.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.handler.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_handler(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    start_date = faker.date_time_this_month()
    handler = HandlerCreate(
        start_date=start_date,
        end_date=start_date + timedelta(days=7),
        username=owner.username,
        position=faker.word()
    )

    db_obj = crud.handler.get_or_create(db, obj_in=handler)

    assert db_obj.id is not None

    same_db_obj = crud.handler.get_or_create(db, obj_in=handler)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_handler(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    handlers = []
    for _ in range(5):
        handlers.append(create_random_handler(db, faker, owner.username))

    random_handler = random.choice(handlers)

    db_obj, count = crud.handler.query_with_filters(db, filter_dict={"id": random_handler.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_handler.id

    db_obj, count = crud.handler.query_with_filters(db, filter_dict={"username": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(handlers)
    assert len(db_obj) == count
    assert all(a.username == owner.username for a in db_obj)

    db_obj, count = crud.handler.query_with_filters(db, filter_dict={"username": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(handlers) - 1
    assert len(db_obj) == count - 1
    assert all(a.username == owner.username for a in db_obj)

    db_obj, count = crud.handler.query_with_filters(db, filter_dict={"username": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.username == owner.username for a in db_obj)

    db_obj, count = crud.handler.query_with_filters(db, filter_dict={"position": f"!{random_handler.position}"})

    assert db_obj is not None
    assert all(a.position != random_handler.position for a in db_obj)


def test_get_with_roles_handler(db: Session, faker: Faker) -> None:
    handlers = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        start_date = faker.date_time_this_month()
        handler = HandlerCreate(
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            username=owner.username,
            position=faker.word()
        )
        roles.append(role)

        handlers.append(crud.handler.create_with_permissions(db, obj_in=handler, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.handler.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_handler(db: Session, faker: Faker) -> None:
    handlers = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        start_date = faker.date_time_this_month()
        handler = HandlerCreate(
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            username=owner.username,
            position=faker.word()
        )
        roles.append(role)

        handlers.append(crud.handler.create_with_permissions(db, obj_in=handler, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.handler.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_handler(db: Session, faker: Faker) -> None:
    start_date = faker.date_time_this_month()
    owner = create_random_user(db, faker)
    handler = HandlerCreate(
        username=owner.username,
        start_date=start_date,
        end_date=start_date + timedelta(days=7),
        position=faker.word()
    )

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.handler.create_with_owner(db, obj_in=handler, owner=owner)

    assert db_obj is not None
    assert db_obj.position == handler.position
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_handler(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    start_date = faker.date_time_this_month()
    handler = HandlerCreate(
        start_date=start_date,
        end_date=start_date + timedelta(days=7),
        username=owner.username,
        position=faker.word()
    )

    db_obj = crud.handler.create_with_permissions(db, obj_in=handler, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.start_date.replace(tzinfo=None) == handler.start_date
    assert db_obj.end_date.replace(tzinfo=None) == handler.end_date
    assert db_obj.username == handler.username
    assert db_obj.position == handler.position


def test_get_history_handler(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    start_date = faker.date_time_this_month()
    handler = HandlerCreate(
        start_date=start_date,
        end_date=start_date + timedelta(days=7),
        username=owner.username,
        position=faker.word()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.handler.create(db, obj_in=handler, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.handler.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_handler(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    handler = create_random_handler(db, faker, user.username)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.handler.remove(db, _id=handler.id, audit_logger=audit_logger)

    assert db_obj.id == handler.id

    db_obj = crud.handler.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_handler_in_date_range(db: Session, faker: Faker) -> None:
    handlers = []
    # make sure that this is unique enough
    start_date = faker.date_time_this_month() + timedelta(days=60)
    end_date = start_date + timedelta(days=7)
    for _ in range(5):
        user = create_random_user(db, faker)
        handler_create = HandlerCreate(
            start_date=start_date,
            end_date=end_date,
            username=user.username,
            position=faker.word()
        )
        handlers.append(crud.handler.create(db, obj_in=handler_create))

    random_handler = random.choice(handlers)
    db_obj, count = crud.handler.get_handlers_in_date_range(db, start_date - timedelta(days=1), end_date + timedelta(days=1))

    assert db_obj is not None
    assert len(db_obj) == len(handlers)
    assert count == len(db_obj)
    assert any(a.id == random_handler.id for a in db_obj)

    db_obj, count = crud.handler.get_handlers_in_date_range(db, start_date - timedelta(days=1), end_date + timedelta(days=1), skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(handlers) - 1
    assert count == len(handlers)

    db_obj, count = crud.handler.get_handlers_in_date_range(db, start_date - timedelta(days=1), end_date + timedelta(days=1), limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert count == len(handlers)

    db_obj, count = crud.handler.get_handlers_in_date_range(db, start_date - timedelta(days=1), end_date + timedelta(days=1), skip=1, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert count == len(handlers)
