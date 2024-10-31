from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.notification import NotificationCreate

try:
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from user import create_random_user


def create_random_notification(db: Session, faker: Faker, user_id: int | None = None):
    if user_id is None:
        user_id = create_random_user(db, faker).id

    notification = NotificationCreate(
        user_id=user_id,
        message=faker.sentence(),
        ack=False,
        ref_id=faker.word()
    )

    return crud.notification.create(db, obj_in=notification)
