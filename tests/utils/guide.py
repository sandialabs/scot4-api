import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.enums import EntryClassEnum, GuideStatusEnum, TargetTypeEnum, TlpEnum
from app.schemas.guide import GuideCreate
from app.schemas.signature import Signature
from app.schemas.link import LinkCreate

try:
    from tests.utils.entry import create_random_entry
    from tests.utils.user import create_random_user
    from tests.utils.signature import create_random_signature
    from tests.utils.popularity import create_random_popularity
    from tests.utils.user_links import create_random_user_links
except ImportError:
    # needed to make initial_data.py function properly
    from entry import create_random_entry
    from user import create_random_user
    from signature import create_random_signature
    from popularity import create_random_popularity
    from user_links import create_random_user_links


def create_random_guide(db: Session, faker: Faker, owner: schemas.User | None = None, signature: Signature | None = None, create_extras: bool | None = True):
    if owner is None:
        owner = create_random_user(db, faker)

    if signature is None:
        signature = create_random_signature(db, faker, owner)
        if create_extras:
            create_random_user_links(db, faker, signature.id, TargetTypeEnum.signature, owner)

    tlp = random.choice(list(TlpEnum))
    subject = f"Guide for {signature.name}"
    status = random.choice(list(GuideStatusEnum))

    guide_create = GuideCreate(
        owner=owner.username,
        tlp=tlp,
        subject=subject,
        status=status,
    )

    guide = crud.guide.create(db, obj_in=guide_create)
    if create_extras:
        entry = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.guide,
            target_id=guide.id,
            entry_class=EntryClassEnum.summary,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, entry.id, owner=owner)
        create_random_user_links(db, faker, entry.id, TargetTypeEnum.entry, owner)
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.guide,
            target_id=guide.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, parent.id, owner=owner)
        create_random_user_links(db, faker, parent.id, TargetTypeEnum.entry, owner)
        entry = create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.guide,
            target_id=guide.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_popularity(db, faker, TargetTypeEnum.entry, entry.id, owner=owner)
        create_random_user_links(db, faker, entry.id, TargetTypeEnum.entry, owner)

    # link signatures
    link_create = LinkCreate(
        v0_type=TargetTypeEnum.signature,
        v0_id=signature.id,
        v1_type=TargetTypeEnum.guide,
        v1_id=guide.id

    )
    crud.link.create(db, obj_in=link_create)

    return guide
