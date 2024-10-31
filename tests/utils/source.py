from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TargetTypeEnum
from app.schemas.source import SourceCreate


def create_random_source(db: Session, faker: Faker, target_type: TargetTypeEnum | None = None, target_id: int | None = None):
    name = f"{faker.unique.word()}{faker.pyint()}".lower()
    description = faker.sentence()

    if target_type is not None and target_id is not None:
        return crud.source.assign_by_name(
            db,
            source_name=name,
            source_description=description,
            target_type=target_type,
            target_id=target_id,
            create=True,
        )
    else:
        source_create = SourceCreate(name=name, description=description)
        return crud.source.create(db, obj_in=source_create)
