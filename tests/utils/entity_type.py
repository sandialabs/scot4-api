import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import EntityTypeStatusEnum
from app.schemas.entity_type import EntityTypeCreate


def create_random_entity_type(db: Session, faker: Faker):
    name = f"{faker.unique.word()}_{faker.pyint()}"
    match_order = faker.pyint(1, 20)
    status = random.choice(list(EntityTypeStatusEnum))
    match = faker.word()
    entity_type_data_ver = str(faker.pyfloat(1, 1, True))

    entity_type_create = EntityTypeCreate(
        name=name,
        match_order=match_order,
        status=status,
        match=match,
        entity_type_data_ver=entity_type_data_ver,
    )

    return crud.entity_type.create(db, obj_in=entity_type_create)
