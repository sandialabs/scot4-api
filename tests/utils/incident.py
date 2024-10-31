import random
from datetime import datetime
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import EntryClassEnum, StatusEnum, TargetTypeEnum, TlpEnum
from app.schemas.incident import IncidentCreate

try:
    from tests.utils.entry import create_random_entry
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from entry import create_random_entry
    from user import create_random_user


def create_random_incident(db: Session, faker: Faker, owner: str | None = None, create_extras: bool | None = True):
    if owner is None:
        owner = create_random_user(db, faker).username

    occurred_date = faker.past_datetime()
    discovered_date = faker.date_time_between_dates(occurred_date, datetime.now())

    incident_create = IncidentCreate(
        owner=owner,
        tlp=random.choice(list(TlpEnum)),
        occurred_date=occurred_date,
        discovered_date=discovered_date,
        reported_date=faker.date_time_between_dates(discovered_date, datetime.now()),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        entry_count=faker.pyint(1, 50),
        view_count=faker.pyint(1, 100),
    )

    incident = crud.incident.create(db, obj_in=incident_create)

    if create_extras:
        crud.tag.assign_by_name(
            db,
            tag_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type=TargetTypeEnum.incident,
            target_id=incident.id,
            create=True,
            tag_description=faker.text(),
        )
        crud.source.assign_by_name(
            db,
            source_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type=TargetTypeEnum.incident,
            target_id=incident.id,
            create=True,
            source_description=faker.text(),
        )
        create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.incident,
            target_id=incident.id,
            entry_class=EntryClassEnum.summary,
        )
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.incident,
            target_id=incident.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.incident,
            target_id=incident.id,
            entry_class=EntryClassEnum.entry,
        )
    return incident
