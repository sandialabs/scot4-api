import random
from faker import Faker
from sqlalchemy.orm import Session
from datetime import timezone

from app import crud
from app.enums import SpecialMetricEnum
from app.schemas.special_metric import SpecialMetricCreate

from tests.utils.utils import select_random_target_type


def create_random_special_metric(db: Session, faker: Faker, metric_type: SpecialMetricEnum | None = None):
    _target_type = select_random_target_type()
    _target_id = faker.pyint()

    if metric_type is None:
        _metric_type = random.choice(list(SpecialMetricEnum))
    else:
        _metric_type = metric_type

    _start_time = faker.date_time_this_month(tzinfo=timezone.utc)
    _end_time = faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc)

    _special_metric_create = SpecialMetricCreate(
        target_id=_target_id,
        target_type=_target_type,
        metric_type=_metric_type,
        start_time=_start_time,
        end_time=_end_time
    )

    return crud.special_metric.create(db, obj_in=_special_metric_create)