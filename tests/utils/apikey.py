from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas import ApiKey


def create_apikey(db: Session, faker: Faker, owner: str):
    apikey_in = ApiKey(
        key=faker.uuid4().upper(),
        owner=owner
    )

    return crud.apikey.create(db_session=db, obj_in=apikey_in)
