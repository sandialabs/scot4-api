import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.enums import EntryClassEnum, StatusEnum, TargetTypeEnum, TlpEnum
from app.schemas.vuln_track import VulnTrackCreate

try:
    from tests.utils.tag import create_random_tag
    from tests.utils.source import create_random_source
    from tests.utils.entry import create_random_entry
    from tests.utils.user import create_random_user
    from tests.utils.popularity import create_random_popularity
    from tests.utils.user_links import create_random_user_links
except ImportError:
    # needed to make initial_data.py function properly
    from tag import create_random_tag
    from source import create_random_source
    from entry import create_random_entry
    from user import create_random_user
    from popularity import create_random_popularity
    from user_links import create_random_user_links


def create_random_vuln_track(db: Session, faker: Faker, owner: schemas.User | None = None, create_extras: bool | None = True):
    tlp = random.choice(list(TlpEnum))
    status = random.choice(list(StatusEnum))
    subject = faker.sentence()

    if owner is None:
        owner = create_random_user(db, faker)

    vuln_track_create = VulnTrackCreate(
        owner=owner.username,
        tlp=tlp,
        status=status,
        subject=subject,
    )
    vuln_track = crud.vuln_track.create(db, obj_in=vuln_track_create)
    if create_extras:
        create_random_tag(db, faker, TargetTypeEnum.vuln_track, vuln_track.id)
        create_random_source(db, faker, TargetTypeEnum.vuln_track, vuln_track.id)
        entry = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.vuln_track,
            target_id=vuln_track.id,
            entry_class=EntryClassEnum.summary,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, entry.id, owner=owner)
        create_random_user_links(db, faker, entry.id, TargetTypeEnum.entry, owner)
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.vuln_track,
            target_id=vuln_track.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, parent.id, owner=owner)
        create_random_user_links(db, faker, parent.id, TargetTypeEnum.entry, owner)
        entry = create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.vuln_track,
            target_id=vuln_track.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, entry.id, owner=owner)
        create_random_user_links(db, faker, entry.id, TargetTypeEnum.entry, owner)
    return vuln_track
