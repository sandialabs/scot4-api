import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TargetTypeEnum
from app.schemas.appearance import AppearanceCreate

try:
    from tests.utils.utils import select_random_target_type
except ImportError:
    # needed to make initial_data.py function properly
    from utils import select_random_target_type


def create_random_appearance(db: Session, faker: Faker, target_id: int | None = None, target_type_enum: TargetTypeEnum | None = None):
    """
    Create a random alertgroup with alerts and a schema included.
    """
    if target_type_enum is None:
        target_type_enum = select_random_target_type()

    appearance_create = AppearanceCreate(
        when_date=faker.iso8601(),
        target_id=target_id,
        target_type=target_type_enum,
        value_id=faker.pyint(),
        value_type=faker.word(),
        value_str=faker.sentence()
    )
    return crud.appearance.create(db, obj_in=appearance_create)
