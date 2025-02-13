import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.enums import EntryClassEnum, StatusEnum, TargetTypeEnum, TlpEnum
from app.schemas.dispatch import DispatchCreate

try:
    from tests.utils.entry import create_random_entry
    from tests.utils.user import create_random_user
    from tests.utils.popularity import create_random_popularity
    from tests.utils.user_links import create_random_user_links
except ImportError:
    # needed to make initial_data.py function properly
    from entry import create_random_entry
    from user import create_random_user
    from popularity import create_random_popularity
    from user_links import create_random_user_links


def create_random_dispatch(db: Session, faker: Faker, owner: schemas.User | None = None, create_extras: bool | None = True):
    if owner is None:
        owner = create_random_user(db, faker)

    tlp = random.choice(list(TlpEnum))
    status = random.choice(list(StatusEnum))
    subject = faker.sentence()

    dispatch_create = DispatchCreate(
        owner=owner.username,
        tlp=tlp,
        status=status,
        subject=subject,
    )
    dispatch = crud.dispatch.create(db, obj_in=dispatch_create)
    if create_extras:
        crud.tag.assign_by_name(
            db,
            tag_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type="dispatch",
            target_id=dispatch.id,
            create=True,
            tag_description=faker.text(),
        )
        crud.source.assign_by_name(
            db,
            source_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type="dispatch",
            target_id=dispatch.id,
            create=True,
            source_description=faker.text(),
        )
        entry = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.dispatch,
            target_id=dispatch.id,
            entry_class=EntryClassEnum.summary,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, entry.id, owner=owner)
        create_random_user_links(db, faker, entry.id, TargetTypeEnum.entry, owner)
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.dispatch,
            target_id=dispatch.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, parent.id, owner=owner)
        create_random_user_links(db, faker, parent.id, TargetTypeEnum.entry, owner)
        entry = create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.dispatch,
            target_id=dispatch.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, entry.id, owner=owner)
        create_random_user_links(db, faker, entry.id, TargetTypeEnum.entry, owner)

    return dispatch
