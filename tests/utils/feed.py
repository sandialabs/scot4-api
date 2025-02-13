from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.schemas.feed import FeedCreate

try:
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from user import create_random_user


def create_random_feed(db: Session, faker: Faker, owner: schemas.User | None = None):
    if owner is None:
        owner = create_random_user(db, faker)

    feed_create = FeedCreate(
        name=faker.word(),
        owner=owner.username,
        type=faker.word(),
        uri=faker.url()
    )

    return crud.feed.create(db, obj_in=feed_create)
