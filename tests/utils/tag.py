from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TargetTypeEnum
from app.schemas.tag import TagCreate


def create_random_tag(db: Session, faker: Faker, target_type: TargetTypeEnum = TargetTypeEnum.none, target_id: int | None = None):
    name = f"{faker.unique.word()}{faker.pyint()}".lower()
    description = faker.sentence()

    if target_type != TargetTypeEnum.none and target_id is not None:
        return crud.tag.assign_by_name(
            db,
            tag_name=name,
            tag_description=description,
            target_id=target_id,
            target_type=target_type,
            create=True,
        )
    else:
        tag_create = TagCreate(name=name, description=description)
        return crud.tag.create(db, obj_in=tag_create)
