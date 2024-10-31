import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import EntryClassEnum, StatusEnum, TargetTypeEnum, TlpEnum
from app.schemas.event import EventCreate

try:
    from tests.utils.tag import create_random_tag
    from tests.utils.source import create_random_source
    from tests.utils.entry import create_random_entry
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from tag import create_random_tag
    from source import create_random_source
    from entry import create_random_entry
    from user import create_random_user


def create_random_event(db: Session, faker: Faker, owner: str | None = None, create_extras: bool | None = True):
    tlp = random.choice(list(TlpEnum))
    status = random.choice(list(StatusEnum))
    subject = faker.sentence()

    if owner is None:
        owner = create_random_user(db, faker).username

    event_create = EventCreate(
        owner=owner,
        tlp=tlp,
        status=status,
        subject=subject,
    )
    event = crud.event.create(db, obj_in=event_create)
    if create_extras:
        create_random_tag(db, faker, TargetTypeEnum.event, event.id)
        create_random_source(db, faker, TargetTypeEnum.event, event.id)
        create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.event,
            target_id=event.id,
            entry_class=EntryClassEnum.summary,
        )
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.event,
            target_id=event.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.event,
            target_id=event.id,
            entry_class=EntryClassEnum.entry,
        )
    return event
