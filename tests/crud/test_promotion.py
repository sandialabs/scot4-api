import random
import pytest
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Promotion
from app.schemas.promotion import PromotionCreate, PromotionUpdate

from tests.utils.alert import create_random_alert
from tests.utils.event import create_random_event
from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.promotion import create_random_promotion
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source


def test_get_promotion(db: Session, faker: Faker) -> None:
    promotion = create_random_promotion(db, faker)
    db_obj = crud.promotion.get(db, promotion.id)

    assert db_obj.id == promotion.id

    db_obj = crud.promotion.get(db, -1)

    assert db_obj is None


def test_get_multi_promotion(db: Session, faker: Faker) -> None:
    promotions = []
    for _ in range(3):
        promotions.append(create_random_promotion(db, faker))

    db_objs = crud.promotion.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == promotions[0].id for i in db_objs)

    db_objs = crud.promotion.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == promotions[1].id for i in db_objs)

    db_objs = crud.promotion.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.promotion.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_promotion(db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)
    promotion = PromotionCreate(
        p0_id=alert.id,
        p0_type=TargetTypeEnum.alert,
        p1_id=event.id,
        p1_type=TargetTypeEnum.event
    )
    db_obj = crud.promotion.create(db, obj_in=promotion)

    assert db_obj.id is not None
    assert db_obj.p0_id == promotion.p0_id
    assert db_obj.p0_type == promotion.p0_type
    assert db_obj.p1_id == promotion.p1_id
    assert db_obj.p1_type == promotion.p1_type


def test_update_promotion(db: Session, faker: Faker) -> None:
    promotion = create_random_promotion(db, faker)
    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)
    update = PromotionUpdate(
        p0_id=alert.id,
        p0_type=TargetTypeEnum.alert,
        p1_id=event.id,
        p1_type=TargetTypeEnum.event
    )

    db_obj = crud.promotion.update(db, db_obj=promotion, obj_in=update)

    assert db_obj.id == promotion.id
    assert db_obj.p0_id == update.p0_id
    assert db_obj.p0_type == update.p0_type
    assert db_obj.p1_id == update.p1_id
    assert db_obj.p1_type == update.p1_type

    update = {}

    db_obj = crud.promotion.update(db, db_obj=promotion, obj_in=update)

    assert db_obj.id == promotion.id

    update = {
        "test": "test"
    }

    db_obj = crud.promotion.update(db, db_obj=promotion, obj_in=update)

    assert db_obj.id == promotion.id
    assert not hasattr(db_obj, "test")

    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)
    update = {
        "p0_id": alert.id,
        "p0_type": TargetTypeEnum.alert,
        "p1_id": event.id,
        "p1_type": TargetTypeEnum.event
    }

    db_obj = crud.promotion.update(db, db_obj=Promotion(), obj_in=update)

    assert db_obj.id == promotion.id + 1
    assert db_obj.p0_id == update["p0_id"]
    assert db_obj.p0_type == update["p0_type"]
    assert db_obj.p1_id == update["p1_id"]
    assert db_obj.p1_type == update["p1_type"]


def test_remove_promotion(db: Session, faker: Faker) -> None:
    promotion = create_random_promotion(db, faker)

    db_obj = crud.promotion.remove(db, _id=promotion.id)

    assert db_obj.id == promotion.id

    db_obj_del = crud.promotion.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.promotion.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_promotion(db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)
    promotion = PromotionCreate(
        p0_id=alert.id,
        p0_type=TargetTypeEnum.alert,
        p1_id=event.id,
        p1_type=TargetTypeEnum.event
    )

    db_obj = crud.promotion.get_or_create(db, obj_in=promotion)

    assert db_obj.id is not None

    same_db_obj = crud.promotion.get_or_create(db, obj_in=promotion)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_promotion(db: Session, faker: Faker) -> None:
    promotions = []
    for _ in range(3):
        promotions.append(create_random_promotion(db, faker))

    random_promotion = random.choice(promotions)

    db_obj, count = crud.promotion.query_with_filters(db, filter_dict={"id": random_promotion.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_promotion.id


def test_get_with_roles_promotion(db: Session, faker: Faker) -> None:
    promotions = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        alert = create_random_alert(db, faker)
        event = create_random_event(db, faker, create_extras=False)
        promotion = PromotionCreate(
            p0_id=alert.id,
            p0_type=TargetTypeEnum.alert,
            p1_id=event.id,
            p1_type=TargetTypeEnum.event
        )
        roles.append(role)

        promotions.append(crud.promotion.create_with_permissions(db, obj_in=promotion, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.promotion.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_promotion(db: Session, faker: Faker) -> None:
    promotions = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        alert = create_random_alert(db, faker)
        event = create_random_event(db, faker, create_extras=False)
        promotion = PromotionCreate(
            p0_id=alert.id,
            p0_type=TargetTypeEnum.alert,
            p1_id=event.id,
            p1_type=TargetTypeEnum.event
        )
        roles.append(role)

        promotions.append(crud.promotion.create_with_permissions(db, obj_in=promotion, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.promotion.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_promotion(db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)
    promotion = PromotionCreate(
        p0_id=alert.id,
        p0_type=TargetTypeEnum.alert,
        p1_id=event.id,
        p1_type=TargetTypeEnum.event
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.promotion.create_with_owner(db, obj_in=promotion, owner=owner)

    assert db_obj is not None
    assert db_obj.p0_id == promotion.p0_id
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_promotion(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)
    promotion = PromotionCreate(
        p0_id=alert.id,
        p0_type=TargetTypeEnum.alert,
        p1_id=event.id,
        p1_type=TargetTypeEnum.event
    )

    db_obj = crud.promotion.create_with_permissions(db, obj_in=promotion, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.p0_id == promotion.p0_id
    assert db_obj.p0_type == promotion.p0_type
    assert db_obj.p1_id == promotion.p1_id
    assert db_obj.p1_type == promotion.p1_type


def test_create_in_object_promotion(db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)
    promotion = PromotionCreate(
        p0_id=alert.id,
        p0_type=TargetTypeEnum.alert,
        p1_id=event.id,
        p1_type=TargetTypeEnum.event
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.promotion.create_in_object(db, obj_in=promotion, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.p0_id == promotion.p0_id


def test_get_history_promotion(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)
    promotion = PromotionCreate(
        p0_id=alert.id,
        p0_type=TargetTypeEnum.alert,
        p1_id=event.id,
        p1_type=TargetTypeEnum.event
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.promotion.create(db, obj_in=promotion, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.promotion.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_promotion(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    promotion = create_random_promotion(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.promotion.remove(db, _id=promotion.id, audit_logger=audit_logger)

    assert db_obj.id == promotion.id

    db_obj = crud.promotion.undelete(db, db_obj.id)

    assert db_obj is None


def test_promote(db: Session, faker: Faker) -> None:
    with pytest.raises(Exception):
        db_obj = crud.promotion.promote(db, [])

    with pytest.raises(Exception):
        db_obj = crud.promotion.promote(db, [{"test": "test"}])

    alert = create_random_alert(db, faker)

    db_obj = crud.promotion.promote(db, [{"type": TargetTypeEnum.alert, "id": alert.id}], TargetTypeEnum.event)

    assert db_obj is not None
    assert db_obj.id is not None
    assert db_obj.target_type_enum() == TargetTypeEnum.event

    alert = create_random_alert(db, faker)
    event = create_random_event(db, faker, create_extras=False)

    db_obj = crud.promotion.promote(db, [{"type": TargetTypeEnum.alert, "id": alert.id}], TargetTypeEnum.event, event.id)

    assert db_obj is not None
    assert db_obj.id == event.id
    assert db_obj.target_type_enum() == TargetTypeEnum.event

    alert = create_random_alert(db, faker)
    user = create_random_user(db, faker)

    db_obj = crud.promotion.promote(db, [{"type": TargetTypeEnum.alert, "id": alert.id}], TargetTypeEnum.event, owner=user)

    assert db_obj is not None
    assert db_obj.id is not None
    assert db_obj.target_type_enum() == TargetTypeEnum.event
    assert db_obj.owner == user.username

    alert = create_random_alert(db, faker)
    tag = create_random_tag(db, faker)

    db_obj = crud.promotion.promote(db, [{"type": TargetTypeEnum.alert, "id": alert.id}], TargetTypeEnum.event, tags=[tag.name])

    assert db_obj is not None

    db_obj = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.event, "v0_id": db_obj.id, "v1_type": TargetTypeEnum.tag, "v1_id": tag.id})

    assert db_obj is not None

    alert = create_random_alert(db, faker)
    source = create_random_source(db, faker)

    db_obj = crud.promotion.promote(db, [{"type": TargetTypeEnum.alert, "id": alert.id}], TargetTypeEnum.event, sources=[source.name])

    assert db_obj is not None

    link_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.event, "v0_id": db_obj.id, "v1_type": TargetTypeEnum.source, "v1_id": source.id})

    assert link_obj is not None
    assert count == 1
    assert link_obj[0].v0_type == TargetTypeEnum.event
    assert link_obj[0].v0_id == db_obj.id
    assert link_obj[0].v1_type == TargetTypeEnum.source
    assert link_obj[0].v1_id == source.id
