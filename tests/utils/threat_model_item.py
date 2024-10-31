from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.threat_model_item import ThreatModelItemCreate


def create_random_threat_model_item(db: Session, faker: Faker):
    threat_model_item = ThreatModelItemCreate(
        title=faker.sentence(),
        type=faker.word(),
        description=faker.sentence(),
        data=faker.json()
    )

    return crud.threat_model_item.create(db, obj_in=threat_model_item)
