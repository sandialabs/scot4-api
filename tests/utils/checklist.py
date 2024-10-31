import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TlpEnum
from app.schemas.checklist import ChecklistCreate

try:
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from user import create_random_user


def create_random_checklist(db: Session, faker: Faker, owner: str | None = None):
    if owner is None:
        owner = create_random_user(db, faker).username

    tlp = random.choice(list(TlpEnum))
    subject = faker.sentence(12)
    checklist_data_ver = str(faker.pyfloat(1, 1, True))
    checklist_data = faker.pydict(value_types=[int, str, float])

    checklist_create = ChecklistCreate(
        owner=owner,
        tlp=tlp,
        subject=subject,
        checklist_data_ver=checklist_data_ver,
        checklist_data=checklist_data,
    )

    return crud.checklist.create(db, obj_in=checklist_create)
