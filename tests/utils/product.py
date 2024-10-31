import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import EntryClassEnum, TargetTypeEnum, TlpEnum
from app.schemas.product import ProductCreate

try:
    from tests.utils.entry import create_random_entry
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from entry import create_random_entry
    from user import create_random_user


def create_random_product(db: Session, faker: Faker, owner: str | None = None, create_extras: bool | None = True):
    if owner is None:
        owner = create_random_user(db, faker).username

    tlp = random.choice(list(TlpEnum))
    subject = faker.sentence()

    product_create = ProductCreate(
        owner=owner,
        tlp=tlp,
        subject=subject,
    )
    product = crud.product.create(db, obj_in=product_create)
    if create_extras:
        crud.tag.assign_by_name(
            db,
            tag_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type=TargetTypeEnum.product,
            target_id=product.id,
            create=True,
            tag_description=faker.text(),
        )
        crud.source.assign_by_name(
            db,
            source_name=f"{faker.word().lower()}_{faker.pyint()}",
            target_type=TargetTypeEnum.product,
            target_id=product.id,
            create=True,
            source_description=faker.text(),
        )
        create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.product,
            target_id=product.id,
            entry_class=EntryClassEnum.summary,
        )
        parent = create_random_entry(
            db,
            faker,
            owner,
            target_type=TargetTypeEnum.product,
            target_id=product.id,
            entry_class=EntryClassEnum.entry,
        )
        create_random_entry(
            db,
            faker,
            owner,
            parent_entry_id=parent.id,
            target_type=TargetTypeEnum.product,
            target_id=product.id,
            entry_class=EntryClassEnum.entry,
        )
    return product
