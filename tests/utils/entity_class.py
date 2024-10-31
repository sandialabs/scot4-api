from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.entity_class import EntityClassCreate


def create_random_entity_class(db: Session, faker: Faker):
    entity_class_create = EntityClassCreate(
        display_name=faker.word(),
        name=f"{faker.word()}_{faker.pyint()}",
        icon=faker.word(),
        description=faker.sentence()
    )
    return crud.entity_class.create(db, obj_in=entity_class_create)
