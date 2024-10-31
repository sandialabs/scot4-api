from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.pivot import PivotCreate


def create_random_pivot(db: Session, faker: Faker, entity_type_ids: list | None = None):
    pivot_created = PivotCreate(
        title=faker.word(),
        template=faker.word(),
        description=faker.sentence()
    )

    pivot = crud.pivot.create(db, obj_in=pivot_created)
    if entity_type_ids:
        crud.pivot.add_entity_types(db, pivot, entity_type_ids)

    return pivot
