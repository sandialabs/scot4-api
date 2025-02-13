import random

from typing import Tuple

from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TargetTypeEnum
from app.schemas.link import LinkCreate

try:
    from tests.utils.alert import create_random_alert
    from tests.utils.alertgroup import create_random_alertgroup_no_sig
    from tests.utils.checklist import create_random_checklist
    from tests.utils.dispatch import create_random_dispatch
    from tests.utils.entity import create_random_entity
    from tests.utils.entry import create_random_entry
    from tests.utils.event import create_random_event
    from tests.utils.feed import create_random_feed
    from tests.utils.file import create_random_file
    from tests.utils.guide import create_random_guide
    from tests.utils.incident import create_random_incident
    from tests.utils.intel import create_random_intel
    from tests.utils.product import create_random_product
    from tests.utils.signature import create_random_signature
    from tests.utils.source import create_random_source
    from tests.utils.tag import create_random_tag
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from alert import create_random_alert
    from alertgroup import create_random_alertgroup_no_sig
    from checklist import create_random_checklist
    from dispatch import create_random_dispatch
    from entity import create_random_entity
    from entry import create_random_entry
    from event import create_random_event
    from feed import create_random_feed
    from file import create_random_file
    from guide import create_random_guide
    from incident import create_random_incident
    from intel import create_random_intel
    from product import create_random_product
    from signature import create_random_signature
    from source import create_random_source
    from tag import create_random_tag
    from user import create_random_user


def get_type_object(db: Session, faker: Faker, type_enum: TargetTypeEnum | None = None) -> Tuple[TargetTypeEnum, int]:
    if not type_enum:
        type_enum = random.choice(list(TargetTypeEnum))
    type_object = None
    if type_enum == TargetTypeEnum.alert:
        user = create_random_user(db, faker)
        type_object = create_random_alert(db, faker, user)
    elif type_enum == TargetTypeEnum.alertgroup:
        type_object = create_random_alertgroup_no_sig(db, faker)
    elif type_enum == TargetTypeEnum.checklist:
        user = create_random_user(db, faker)
        type_object = create_random_checklist(db, faker, user)
    elif type_enum == TargetTypeEnum.dispatch:
        user = create_random_user(db, faker)
        type_object = create_random_dispatch(db, faker, user, False)
    elif type_enum == TargetTypeEnum.entity:
        type_object = create_random_entity(db, faker)
    elif type_enum == TargetTypeEnum.entry:
        user = create_random_user(db, faker)
        type_object = create_random_entry(db, faker, user)
    elif type_enum == TargetTypeEnum.event:
        user = create_random_user(db, faker)
        type_object = create_random_event(db, faker, user, False)
    elif type_enum == TargetTypeEnum.feed:
        user = create_random_user(db, faker)
        type_object = create_random_feed(db, faker, user)
    elif type_enum == TargetTypeEnum.file:
        user = create_random_user(db, faker)
        type_object = create_random_file(db, faker, user)
    elif type_enum == TargetTypeEnum.guide:
        user = create_random_user(db, faker)
        signature = create_random_signature(db, faker, user)
        type_object = create_random_guide(db, faker, user, signature, False)
    elif type_enum == TargetTypeEnum.incident:
        user = create_random_user(db, faker)
        type_object = create_random_incident(db, faker, user, False)
    elif type_enum == TargetTypeEnum.intel:
        user = create_random_user(db, faker)
        type_object = create_random_intel(db, faker, user, False)
    elif type_enum == TargetTypeEnum.product:
        user = create_random_user(db, faker)
        type_object = create_random_product(db, faker, user)
    elif type_enum == TargetTypeEnum.signature:
        user = create_random_user(db, faker)
        type_object = create_random_signature(db, faker, user)
    elif type_enum == TargetTypeEnum.source:
        type_object = create_random_source(db, faker)
    elif type_enum == TargetTypeEnum.tag:
        type_object = create_random_tag(db, faker)
    else:
        # if anything else make it an alert
        type_enum = TargetTypeEnum.alert
        user = create_random_user(db, faker)
        type_object = create_random_alert(db, faker, user)

    # make extra sure we dont end up with a None type
    if type_enum is None:
        type_enum = TargetTypeEnum.alert
        user = create_random_user(db, faker)
        type_object = create_random_alert(db, faker, user)

    return type_enum, type_object.id


def create_random_link(db: Session, faker: Faker, v0_type: TargetTypeEnum = None, v0_id: int = None):
    if v0_type is None or v0_id is None:
        v0_type, v0_id = get_type_object(db, faker)
    v1_type, v1_id = get_type_object(db, faker)

    link = LinkCreate(
        v0_id=v0_id,
        v0_type=v0_type,
        v1_id=v1_id,
        v1_type=v1_type,
        context=faker.sentence()
    )

    return crud.link.create(db, obj_in=link)


def create_link(db: Session, faker: Faker, v1_type: TargetTypeEnum, v1_id: int = None, v0_type: TargetTypeEnum = None, v0_id: int = None):
    if v0_type is None or v0_id is None:
        v0_type, v0_id = get_type_object(db, faker)
    if v1_id is None:
        v1_type, v1_id = get_type_object(db, faker, v1_type)

    link = LinkCreate(
        v0_id=v0_id,
        v0_type=v0_type,
        v1_id=v1_id,
        v1_type=v1_type,
        context=faker.sentence()
    )

    return crud.link.create(db, obj_in=link)
