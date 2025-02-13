from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.schemas import ApiKey


def create_apikey(db: Session, faker: Faker, owner: schemas.User):
    apikey_in = ApiKey(
        key=faker.uuid4().upper(),
        owner=owner.username
    )

    return crud.apikey.create(db_session=db, obj_in=apikey_in)
