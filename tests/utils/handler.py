import datetime
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.handler import HandlerCreate

try:
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from user import create_random_user


def create_random_handler(db: Session, faker: Faker, username: str | None = None):
    if username is None:
        username = create_random_user(db, faker).username

    start_date = faker.date_time_this_month()

    handler_create = HandlerCreate(
        start_date=start_date,
        end_date=start_date + datetime.timedelta(days=7),
        username=username,
        position=faker.word(),
    )

    return crud.handler.create(db, obj_in=handler_create)
