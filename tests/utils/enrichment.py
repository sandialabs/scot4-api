import random
from faker import Faker
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.enums import EnrichmentClassEnum
from app.schemas import EnrichmentCreate

from tests.utils.entity import create_random_entity


def create_random_enrichment(db: Session, faker: Faker, entity_id: int | None = None):
    if entity_id is None:
        entity_id = create_random_entity(db, faker).id

    enrichment = EnrichmentCreate(
        title=faker.sentence(),
        entity_id=entity_id,
        enrichment_class=random.choice(list(EnrichmentClassEnum)),
        data=jsonable_encoder(faker.pydict()),
        description=faker.sentence()
    )

    return crud.enrichment.create(db_session=db, obj_in=enrichment)
