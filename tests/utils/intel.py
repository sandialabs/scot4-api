import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import EntryClassEnum, StatusEnum, TargetTypeEnum, TlpEnum
from app.schemas.intel import IntelCreate

try:
    from tests.utils.entry import create_random_entry
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from entry import create_random_entry
    from user import create_random_user


def create_random_intel(db: Session, faker: Faker, owner: str | None = None, create_extras: bool | None = True):
    if owner is None:
        owner = create_random_user(db, faker).username

    intel_create = IntelCreate(
        owner=owner,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )
    intel = crud.intel.create(db, obj_in=intel_create)
    if create_extras:
        crud.tag.assign_by_name(
            db,
            tag_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type="intel",
            target_id=intel.id,
            create=True,
            tag_description=faker.text(),
        )
        crud.source.assign_by_name(
            db,
            source_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type="intel",
            target_id=intel.id,
            create=True,
            source_description=faker.text(),
        )
        create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.intel,
            target_id=intel.id,
            entry_class=EntryClassEnum.summary,
        )
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.intel,
            target_id=intel.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.intel,
            target_id=intel.id,
            entry_class=EntryClassEnum.entry,
        )

    return intel
