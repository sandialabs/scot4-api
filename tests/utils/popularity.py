import random

from faker import Faker
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum, PopularityMetricEnum
from app import schemas, crud

try:
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from user import create_random_user


def create_random_popularity(db: Session, faker: Faker, target_type: TargetTypeEnum = None, target_id: int = None, metric: PopularityMetricEnum = None, owner: schemas.User = None) -> schemas.Popularity:
    if owner is None:
        owner = create_random_user(db, faker)
    if target_type is None:
        target_list = list(TargetTypeEnum)
        target_list.remove(TargetTypeEnum.none)
        target_list.remove(TargetTypeEnum.remote_flair)
        target_type = random.choice(target_list)
    if target_id is None:
        target_id = faker.pyint()
    if metric is None:
        metric = random.choice(list(PopularityMetricEnum))

    popularity = schemas.PopularityCreate(
        target_type=target_type,
        target_id=target_id,
        metric_type=metric,
        owner_id=owner.id
    )

    return crud.popularity.create(db, obj_in=popularity)
