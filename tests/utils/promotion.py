import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TargetTypeEnum
from app.schemas.promotion import PromotionCreate

try:
    from tests.utils.alert import create_random_alert
    from tests.utils.event import create_random_event
    from tests.utils.dispatch import create_random_dispatch
    from tests.utils.incident import create_random_incident
    from tests.utils.intel import create_random_intel
except ImportError:
    # needed to make initial_data.py function properly
    from alert import create_random_alert
    from event import create_random_event
    from dispatch import create_random_dispatch
    from incident import create_random_incident
    from intel import create_random_intel


def promote_alert_to_event(db: Session, alert_ids: list[int]):
    source = [{"id": alert_id, "type": TargetTypeEnum.alert} for alert_id in alert_ids]
    return crud.promotion.promote(
        db_session=db, source=source, destination=TargetTypeEnum.event
    )


def promote_event_to_incident(db: Session, event_ids: list[int]):
    source = [{"id": event_id, "type": TargetTypeEnum.event} for event_id in event_ids]
    return crud.promotion.promote(
        db_session=db, source=source, destination=TargetTypeEnum.incident
    )


def promote_vuln_feed_to_incident(db: Session, vuln_feed_ids: list[int]):
    source = [{"id": vuln_feed_id, "type": TargetTypeEnum.vuln_feed} for vuln_feed_id in vuln_feed_ids]
    return crud.promotion.promote(
        db_session=db, source=source, destination=TargetTypeEnum.incident
    )


def promote_vuln_track_to_incident(db: Session, vuln_track_ids: list[int]):
    source = [{"id": vuln_track_id, "type": TargetTypeEnum.vuln_track} for vuln_track_id in vuln_track_ids]
    return crud.promotion.promote(
        db_session=db, source=source, destination=TargetTypeEnum.incident
    )


def promote_dispatch_to_intel(db: Session, dispatch_ids: list[int]):
    source = [
        {"id": dispatch_id, "type": TargetTypeEnum.dispatch} for dispatch_id in dispatch_ids
    ]
    return crud.promotion.promote(
        db_session=db, source=source, destination=TargetTypeEnum.intel
    )


def promote_intel_to_product(db: Session, intel_ids: list[int]):
    source = [
        {"id": intel_id, "type": TargetTypeEnum.intel} for intel_id in intel_ids
    ]
    return crud.promotion.promote(
        db_session=db, source=source, destination=TargetTypeEnum.product
    )


def create_random_promotion(db: Session, faker: Faker):
    source = random.choice([TargetTypeEnum.alert, TargetTypeEnum.event, TargetTypeEnum.dispatch])

    if source == TargetTypeEnum.alert:
        source_obj = create_random_alert(db, faker)
        dest = TargetTypeEnum.event
        dest_obj = create_random_event(db, faker, create_extras=False)
    elif source == TargetTypeEnum.event:
        source_obj = create_random_event(db, faker, create_extras=False)
        dest = TargetTypeEnum.incident
        dest_obj = create_random_incident(db, faker, create_extras=False)
    elif source == TargetTypeEnum.dispatch:
        source_obj = create_random_dispatch(db, faker, create_extras=False)
        dest = TargetTypeEnum.intel
        dest_obj = create_random_intel(db, faker, create_extras=False)

    promote_create = PromotionCreate(
        p0_id=source_obj.id,
        p0_type=source,
        p1_id=dest_obj.id,
        p1_type=dest
    )

    return crud.promotion.create(db, obj_in=promote_create)
