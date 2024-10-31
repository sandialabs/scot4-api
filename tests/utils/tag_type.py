from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.tag_type import TagTypeCreate


def create_random_tag_type(db: Session, faker: Faker):
    tag_type_create = TagTypeCreate(
        name=faker.word(),
        description=faker.sentence()
    )
    return crud.tag_type.create(db, obj_in=tag_type_create)
