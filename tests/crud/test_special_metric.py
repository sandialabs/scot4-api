import random

from faker import Faker
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app import crud
from app.api.deps import AuditLogger
from app.enums import TargetTypeEnum, SpecialMetricEnum
from app.models import SpecialMetric
from app.schemas.special_metric import SpecialMetricCreate, SpecialMetricUpdate

from tests.utils.special_metric import create_random_special_metric
from tests.utils.user import create_random_user


def test_get_special_metric(db: Session, faker: Faker) -> None:
    special_metric = create_random_special_metric(db, faker)
    db_obj = crud.special_metric.get(db, special_metric.id)

    assert db_obj.id == special_metric.id

    db_obj = crud.special_metric.get(db, -1)

    assert db_obj is None


def test_get_multi_special_metric(db: Session, faker: Faker) -> None:
    special_metrics = []
    for _ in range(3):
        special_metrics.append(create_random_special_metric(db, faker))

    db_objs = crud.special_metric.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == special_metrics[0].id for i in db_objs)

    db_objs = crud.special_metric.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == special_metrics[1].id for i in db_objs)

    db_objs = crud.special_metric.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.special_metric.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_special_metric(db: Session, faker: Faker) -> None:
    _start_time = faker.date_time_this_month(tzinfo=timezone.utc)

    special_metric = SpecialMetricCreate(
        target_type=random.choice(list(TargetTypeEnum)),
        target_id=faker.pyint(),
        metric_type=random.choice(list(SpecialMetricEnum)),
        start_time=_start_time,
        end_time=faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc)
    )
    db_obj = crud.special_metric.create(db, obj_in=special_metric)

    assert db_obj.id is not None
    assert db_obj.target_type == special_metric.target_type
    assert db_obj.target_id == special_metric.target_id
    assert db_obj.metric_type == special_metric.metric_type
    assert db_obj.start_time == special_metric.start_time
    assert db_obj.end_time == special_metric.end_time


def test_update_special_metric(db: Session, faker: Faker) -> None:
    special_metric = create_random_special_metric(db, faker)

    update = SpecialMetricUpdate(
        start_time=faker.date_time_this_month(tzinfo=timezone.utc),
        end_time=datetime.now(tz=timezone.utc)
    )

    db_obj = crud.special_metric.update(db, db_obj=special_metric, obj_in=update)

    assert db_obj.id == special_metric.id
    assert db_obj.target_type == special_metric.target_type
    assert db_obj.target_id == special_metric.target_id
    assert db_obj.metric_type == special_metric.metric_type
    assert db_obj.start_time == update.start_time
    assert db_obj.end_time == update.end_time

    update = {}

    db_obj = crud.special_metric.update(db, db_obj=special_metric, obj_in=update)

    assert db_obj.id == special_metric.id

    update = {
        "test": "test"
    }

    db_obj = crud.special_metric.update(db, db_obj=special_metric, obj_in=update)

    assert db_obj.id == special_metric.id
    assert not hasattr(db_obj, "test")

    update = {
        "end_time": datetime.now(tz=timezone.utc)
    }

    _start_time = faker.date_time_this_month(tzinfo=timezone.utc)

    update = { 
        "target_type": random.choice(list(TargetTypeEnum)),
        "target_id": faker.pyint(),
        "metric_type": random.choice(list(SpecialMetricEnum)),
        "start_time": _start_time,
        "end_time": faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc)
    }

    db_obj = crud.special_metric.update(db, db_obj=SpecialMetric(), obj_in=update)

    assert db_obj.id == special_metric.id + 1
    assert db_obj.target_type == update["target_type"]
    assert db_obj.target_id == update["target_id"]
    assert db_obj.metric_type == update["metric_type"]
    assert db_obj.start_time == update["start_time"]
    assert db_obj.end_time == update["end_time"]


def test_remove_special_metric(db: Session, faker: Faker) -> None:
    special_metric = create_random_special_metric(db, faker)

    db_obj = crud.special_metric.remove(db, _id=special_metric.id)

    assert db_obj.id == special_metric.id

    db_obj_del = crud.special_metric.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.special_metric.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_special_metric(db: Session, faker: Faker) -> None:
    _start_time = faker.date_time_this_month(tzinfo=timezone.utc)

    special_metric = SpecialMetricCreate(
        target_type=random.choice(list(TargetTypeEnum)),
        target_id=faker.pyint(),
        metric_type=random.choice(list(SpecialMetricEnum)),
        start_time=_start_time,
        end_time=faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc)
    )

    db_obj = crud.special_metric.get_or_create(db, obj_in=special_metric)

    assert db_obj.id is not None

    same_db_obj = crud.special_metric.get_or_create(db, obj_in=special_metric)

    assert same_db_obj.id == db_obj.id

    _start_time = faker.date_time_this_month(tzinfo=timezone.utc)
    special_metric_new_time = SpecialMetricCreate(
        target_type=special_metric.target_type,
        target_id=special_metric.target_id,
        metric_type=special_metric.metric_type,
        start_time=_start_time,
        end_time=faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc)
    )

    new_time_db_obj = crud.special_metric.get_or_create(db, obj_in=special_metric_new_time)

    assert new_time_db_obj.id == db_obj.id


def test_query_with_filters_special_metric(db: Session, faker: Faker) -> None:
    special_metrics = []
    for _ in range(3):
        special_metrics.append(create_random_special_metric(db, faker, metric_type=SpecialMetricEnum.mttc))

    random_special_metric = random.choice(special_metrics)

    db_obj, count = crud.special_metric.query_with_filters(db, filter_dict={"id": random_special_metric.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_special_metric.id

    db_obj, count = crud.special_metric.query_with_filters(db, filter_dict={"metric_type": SpecialMetricEnum.mttc})

    assert db_obj is not None
    assert len(db_obj) == count
    assert all(a.metric_type == SpecialMetricEnum.mttc for a in db_obj)

    db_obj, count = crud.special_metric.query_with_filters(db, filter_dict={"metric_type": SpecialMetricEnum.mttc}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == count - 1
    assert all(a.metric_type == SpecialMetricEnum.mttc for a in db_obj)

    db_obj, count = crud.special_metric.query_with_filters(db, filter_dict={"metric_type": SpecialMetricEnum.mttc}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.metric_type == SpecialMetricEnum.mttc for a in db_obj)

    db_obj, count = crud.special_metric.query_with_filters(db, filter_dict={"target_id": random_special_metric.target_id, "target_type": random_special_metric.target_type})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_special_metric.id
    assert db_obj[0].target_type == random_special_metric.target_type
    assert db_obj[0].target_id == random_special_metric.target_id

    db_obj, count = crud.special_metric.query_with_filters(db, filter_dict={"id": f"!{random_special_metric.id}"})

    assert db_obj is not None
    assert all(a.id != random_special_metric.id for a in db_obj)


def test_get_history_special_metric(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    _start_time = faker.date_time_this_month(tzinfo=timezone.utc)

    special_metric = SpecialMetricCreate(
        target_type=random.choice(list(TargetTypeEnum)),
        target_id=faker.pyint(),
        metric_type=random.choice(list(SpecialMetricEnum)),
        start_time=_start_time,
        end_time=faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc)
    )

    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.special_metric.create(db, obj_in=special_metric, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.special_metric.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_special_metric(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    special_metric = create_random_special_metric(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.special_metric.remove(db, _id=special_metric.id, audit_logger=audit_logger)

    assert db_obj.id == special_metric.id

    db_obj = crud.special_metric.undelete(db, db_obj.id)

    assert db_obj is None
