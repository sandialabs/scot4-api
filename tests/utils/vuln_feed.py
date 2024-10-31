import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import EntryClassEnum, StatusEnum, TargetTypeEnum, TlpEnum
from app.schemas.vuln_feed import VulnFeedCreate

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


def create_random_vuln_feed(db: Session, faker: Faker, owner: str | None = None, create_extras: bool | None = True):
    tlp = random.choice(list(TlpEnum))
    status = random.choice(list(StatusEnum))
    subject = faker.sentence()

    if owner is None:
        owner = create_random_user(db, faker).username

    vuln_feed_create = VulnFeedCreate(
        owner=owner,
        tlp=tlp,
        status=status,
        subject=subject,
    )
    vuln_feed = crud.vuln_feed.create(db, obj_in=vuln_feed_create)
    if create_extras:
        create_random_tag(db, faker, TargetTypeEnum.vuln_feed, vuln_feed.id)
        create_random_source(db, faker, TargetTypeEnum.vuln_feed, vuln_feed.id)
        create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.vuln_feed,
            target_id=vuln_feed.id,
            entry_class=EntryClassEnum.summary,
        )
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.vuln_feed,
            target_id=vuln_feed.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.vuln_feed,
            target_id=vuln_feed.id,
            entry_class=EntryClassEnum.entry,
        )
    return vuln_feed
