import random
import datetime
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Stat
from app.schemas.stat import StatCreate, StatUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.scot_stat import create_random_stat
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_stat(db: Session, faker: Faker) -> None:
    stat = create_random_stat(db, faker)
    db_obj = crud.stat.get(db, stat.id)

    assert db_obj.id == stat.id

    db_obj = crud.stat.get(db, -1)

    assert db_obj is None


def test_get_multi_stat(db: Session, faker: Faker) -> None:
    stats = []
    for _ in range(5):
        stats.append(create_random_stat(db, faker))

    db_objs = crud.stat.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == stats[0].id for i in db_objs)

    db_objs = crud.stat.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == stats[1].id for i in db_objs)

    db_objs = crud.stat.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.stat.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_stat(db: Session, faker: Faker) -> None:
    dt: datetime.datetime = faker.date_time_this_month()
    stat = StatCreate(
        year=dt.year,
        quarter=dt.month // 4 + 1,
        month=dt.month,
        day_of_week=dt.weekday(),
        day=dt.day,
        hour=dt.hour,
        stat_metric=faker.word(),
        value=faker.pyint()
    )
    db_obj = crud.stat.create(db, obj_in=stat)

    assert db_obj.id is not None
    assert db_obj.year == stat.year
    assert db_obj.quarter == stat.quarter
    assert db_obj.month == stat.month
    assert db_obj.day_of_week == stat.day_of_week
    assert db_obj.day == stat.day
    assert db_obj.hour == stat.hour
    assert db_obj.stat_metric == stat.stat_metric
    assert db_obj.value == stat.value


def test_update_stat(db: Session, faker: Faker) -> None:
    stat = create_random_stat(db, faker)
    dt: datetime.datetime = faker.date_time_this_month()
    update = StatUpdate(
        year=dt.year,
        quarter=dt.month // 4 + 1,
        month=dt.month,
        day_of_week=dt.weekday(),
        day=dt.day,
        hour=dt.hour,
        stat_metric=faker.word(),
        value=faker.pyint()
    )

    db_obj = crud.stat.update(db, db_obj=stat, obj_in=update)

    assert db_obj.id == stat.id
    assert db_obj.year == update.year
    assert db_obj.quarter == update.quarter
    assert db_obj.month == update.month
    assert db_obj.day_of_week == update.day_of_week
    assert db_obj.day == update.day
    assert db_obj.hour == update.hour
    assert db_obj.stat_metric == update.stat_metric
    assert db_obj.value == update.value

    update = {}

    db_obj = crud.stat.update(db, db_obj=stat, obj_in=update)

    assert db_obj.id == stat.id

    update = {
        "test": "test"
    }

    db_obj = crud.stat.update(db, db_obj=stat, obj_in=update)

    assert db_obj.id == stat.id
    assert not hasattr(db_obj, "test")

    dt: datetime.datetime = faker.date_time_this_month()
    update = {
        "year": dt.year,
        "quarter": dt.month // 4 + 1,
        "month": dt.month,
        "day_of_week": dt.weekday(),
        "day": dt.day,
        "hour": dt.hour,
        "stat_metric": faker.word(),
        "value": faker.pyint()
    }

    db_obj = crud.stat.update(db, db_obj=Stat(), obj_in=update)

    assert db_obj.id == stat.id + 1
    assert db_obj.year == update["year"]
    assert db_obj.quarter == update["quarter"]
    assert db_obj.month == update["month"]
    assert db_obj.day_of_week == update["day_of_week"]
    assert db_obj.day == update["day"]
    assert db_obj.hour == update["hour"]
    assert db_obj.stat_metric == update["stat_metric"]
    assert db_obj.value == update["value"]


def test_remove_stat(db: Session, faker: Faker) -> None:
    stat = create_random_stat(db, faker)

    db_obj = crud.stat.remove(db, _id=stat.id)

    assert db_obj.id == stat.id

    db_obj_del = crud.stat.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.stat.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_stat(db: Session, faker: Faker) -> None:
    dt: datetime.datetime = faker.date_time_this_month()
    stat = StatCreate(
        year=dt.year,
        quarter=dt.month // 4 + 1,
        month=dt.month,
        day_of_week=dt.weekday(),
        day=dt.day,
        hour=dt.hour,
        stat_metric=faker.word(),
        value=faker.pyint()
    )

    db_obj = crud.stat.get_or_create(db, obj_in=stat)

    assert db_obj.id is not None

    same_db_obj = crud.stat.get_or_create(db, obj_in=stat)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_stat(db: Session, faker: Faker) -> None:
    stats = []
    for _ in range(5):
        stats.append(create_random_stat(db, faker))

    random_stat = random.choice(stats)

    db_obj, count = crud.stat.query_with_filters(db, filter_dict={"id": random_stat.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_stat.id

    db_obj, count = crud.stat.query_with_filters(db, filter_dict={"stat_metric": f"!{random_stat.stat_metric}"})

    assert db_obj is not None
    assert all(a.stat_metric != random_stat.stat_metric for a in db_obj)


def test_get_with_roles_stat(db: Session, faker: Faker) -> None:
    stats = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        dt: datetime.datetime = faker.date_time_this_month()
        stat = StatCreate(
            year=dt.year,
            quarter=dt.month // 4 + 1,
            month=dt.month,
            day_of_week=dt.weekday(),
            day=dt.day,
            hour=dt.hour,
            stat_metric=faker.word(),
            value=faker.pyint()
        )
        roles.append(role)

        stats.append(crud.stat.create_with_permissions(db, obj_in=stat, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.stat.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_stat(db: Session, faker: Faker) -> None:
    stats = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        dt: datetime.datetime = faker.date_time_this_month()
        stat = StatCreate(
            year=dt.year,
            quarter=dt.month // 4 + 1,
            month=dt.month,
            day_of_week=dt.weekday(),
            day=dt.day,
            hour=dt.hour,
            stat_metric=faker.word(),
            value=faker.pyint()
        )
        roles.append(role)

        stats.append(crud.stat.create_with_permissions(db, obj_in=stat, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.stat.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_stat(db: Session, faker: Faker) -> None:
    dt: datetime.datetime = faker.date_time_this_month()
    stat = StatCreate(
        year=dt.year,
        quarter=dt.month // 4 + 1,
        month=dt.month,
        day_of_week=dt.weekday(),
        day=dt.day,
        hour=dt.hour,
        stat_metric=faker.word(),
        value=faker.pyint()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.stat.create_with_owner(db, obj_in=stat, owner=owner)

    assert db_obj is not None
    assert db_obj.year == stat.year
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_stat(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    dt: datetime.datetime = faker.date_time_this_month()
    stat = StatCreate(
        year=dt.year,
        quarter=dt.month // 4 + 1,
        month=dt.month,
        day_of_week=dt.weekday(),
        day=dt.day,
        hour=dt.hour,
        stat_metric=faker.word(),
        value=faker.pyint()
    )

    db_obj = crud.stat.create_with_permissions(db, obj_in=stat, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.year == stat.year
    assert db_obj.quarter == stat.quarter
    assert db_obj.month == stat.month
    assert db_obj.day_of_week == stat.day_of_week
    assert db_obj.day == stat.day
    assert db_obj.hour == stat.hour
    assert db_obj.stat_metric == stat.stat_metric
    assert db_obj.value == stat.value

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.stat, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_stat(db: Session, faker: Faker) -> None:
    dt: datetime.datetime = faker.date_time_this_month()
    stat = StatCreate(
        year=dt.year,
        quarter=dt.month // 4 + 1,
        month=dt.month,
        day_of_week=dt.weekday(),
        day=dt.day,
        hour=dt.hour,
        stat_metric=faker.word(),
        value=faker.pyint()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.stat.create_in_object(db, obj_in=stat, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.year == stat.year

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_stat(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dt: datetime.datetime = faker.date_time_this_month()
    stat = StatCreate(
        year=dt.year,
        quarter=dt.month // 4 + 1,
        month=dt.month,
        day_of_week=dt.weekday(),
        day=dt.day,
        hour=dt.hour,
        stat_metric=faker.word(),
        value=faker.pyint()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.stat.create(db, obj_in=stat, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.stat.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_stat(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    stat = create_random_stat(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.stat.remove(db, _id=stat.id, audit_logger=audit_logger)

    assert db_obj.id == stat.id

    db_obj = crud.stat.undelete(db, db_obj.id)

    assert db_obj is None
