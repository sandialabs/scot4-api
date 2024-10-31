import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TargetTypeEnum
from app.schemas.appearance import AppearanceCreate


def create_random_appearance(db: Session, faker: Faker, target_id: int | None = None, target_type_enum: TargetTypeEnum | None = None):
    """
    Create a random alertgroup with alerts and a schema included.
    """
    if target_type_enum is None:
        target_list = list(TargetTypeEnum)
        target_list.remove(TargetTypeEnum.none)
        target_list.remove(TargetTypeEnum.remote_flair)
        target_type_enum = random.choice(target_list)

    appearance_create = AppearanceCreate(
        when_date=faker.iso8601(),
        target_id=target_id,
        target_type=target_type_enum,
        value_id=faker.pyint(),
        value_type=faker.word(),
        value_str=faker.sentence()
    )
    return crud.appearance.create(db, obj_in=appearance_create)
