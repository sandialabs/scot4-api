from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.role import RoleCreate


def create_random_role(db: Session, faker: Faker):
    name = f"{faker.unique.word()}_{faker.pyint()}"
    description = faker.sentence(12)
    role_create = RoleCreate(name=name, description=description)
    return crud.role.create(db, obj_in=role_create)
