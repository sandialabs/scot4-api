from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.sigbody import SigbodyCreate


def create_random_sigbody(db: Session, faker: Faker, signature_id: int):
    sigbody = SigbodyCreate(
        revision=faker.pyint(),
        body=faker.sentence(),
        body64=faker.sentence(),
        signature_id=signature_id
    )

    return crud.sigbody.create(db, obj_in=sigbody)
