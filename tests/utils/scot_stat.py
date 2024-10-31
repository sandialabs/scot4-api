import datetime
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.stat import StatCreate


def create_random_stat(db: Session, faker: Faker):
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

    return crud.stat.create(db, obj_in=stat)
