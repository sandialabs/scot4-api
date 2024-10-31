import random
from datetime import datetime, timezone
from faker import Faker
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.enums import TlpEnum
from app.schemas import AlertGroupDetailed, AlertGroupDetailedCreate, AlertGroupUpdate

from tests.utils.alertgroup_schema import create_random_schema
from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.user import create_random_user


def test_create_alertgroup_new(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker)
    db_obj = crud.alert_group.get(db, _id=alertgroup.id)
    t1 = AlertGroupDetailed.from_orm(db_obj)
    t2 = AlertGroupDetailed.from_orm(alertgroup)
    assert t1 == t2


def test_get_alertgroup_no_sig(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker)
    alertgroup_2 = crud.alert_group.get(db, alertgroup.id)
    assert alertgroup_2
    assert alertgroup.id == alertgroup_2.id
    assert jsonable_encoder(alertgroup) == jsonable_encoder(alertgroup_2)


def test_create_alertgroup(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    tlp = random.choice(list(TlpEnum))
    view_count = faker.pyint(0, 10)
    first_view = datetime.now(tz=timezone.utc)
    message_id = str(faker.pyint(0, 10))
    subject = faker.sentence()
    back_refs = faker.sentence()
    schema = create_random_schema(faker)
    alertgroup = AlertGroupDetailedCreate(
        owner=user.email,
        tlp=tlp,
        view_count=view_count,
        first_view=first_view,
        message_id=message_id,
        subject=subject,
        back_refs=back_refs,
        alert_schema=schema,
    )
    alertgroup_in = crud.alert_group.create(db, obj_in=alertgroup)

    assert alertgroup_in
    assert alertgroup_in.owner == user.email
    assert alertgroup_in.tlp == tlp
    assert alertgroup_in.view_count == view_count
    assert alertgroup_in.first_view == first_view
    assert alertgroup_in.message_id == message_id
    assert alertgroup_in.subject == subject
    assert len(alertgroup.alert_schema) == len(schema)
    schema_dict = {
        s.schema_key_order: (s.schema_key_name, s.schema_key_type) for s in schema
    }
    for schema in alertgroup.alert_schema:
        assert schema_dict[schema.schema_key_order][0] == schema.schema_key_name
        assert schema_dict[schema.schema_key_order][1] == schema.schema_key_type


def test_get_alertgroup(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    tlp = random.choice(list(TlpEnum))
    view_count = faker.pyint(0, 10)
    first_view = datetime.utcnow()
    message_id = str(faker.pyint(0, 10))
    subject = faker.sentence()
    back_refs = faker.sentence()
    schema = create_random_schema(faker)
    alertgroup = AlertGroupDetailedCreate(
        owner=user.email,
        tlp=tlp,
        view_count=view_count,
        first_view=first_view,
        message_id=message_id,
        subject=subject,
        back_refs=back_refs,
        alert_schema=schema,
    )
    alertgroup_in = crud.alert_group.create(db, obj_in=alertgroup)
    alertgroup_2 = crud.alert_group.get(db, alertgroup_in.id)

    assert alertgroup_2
    assert alertgroup_in.owner == alertgroup_2.owner
    assert alertgroup_in.tlp == alertgroup_2.tlp
    assert alertgroup_in.alert_count == alertgroup_2.alert_count
    assert alertgroup_in.closed_count == alertgroup_2.closed_count
    assert alertgroup_in.open_count == alertgroup_2.open_count
    assert alertgroup_in.promoted_count == alertgroup_2.promoted_count
    assert alertgroup_in.view_count == alertgroup_2.view_count
    assert alertgroup_in.first_view == alertgroup_2.first_view
    assert alertgroup_in.message_id == alertgroup_2.message_id
    assert alertgroup_in.subject == alertgroup_2.subject
    assert alertgroup_in.alert_schema == alertgroup_2.alert_schema


def test_get_alertgroups(db: Session, faker: Faker) -> None:
    alertgroups = []
    for _ in range(5):
        user = create_random_user(db, faker)
        tlp = random.choice(list(TlpEnum))
        view_count = faker.pyint(0, 10)
        first_view = datetime.utcnow()
        message_id = str(faker.pyint(0, 10))
        subject = faker.sentence()
        back_refs = faker.sentence()
        schema = create_random_schema(faker)
        alertgroup = AlertGroupDetailedCreate(
            owner=user.email,
            tlp=tlp,
            view_count=view_count,
            first_view=first_view,
            message_id=message_id,
            subject=subject,
            back_refs=back_refs,
            alert_schema=schema,
        )
        alertgroups.append(crud.alert_group.create(db, obj_in=alertgroup))

    alertgroups_get = crud.alert_group.get_multi(db)

    assert alertgroups_get
    assert len(alertgroups_get) >= len(alertgroups)


def test_update_alertgroup(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    tlp = random.choice(list(TlpEnum))
    view_count = faker.pyint(0, 10)
    first_view = datetime.utcnow()
    message_id = str(faker.pyint(0, 10))
    subject = faker.sentence()
    back_refs = faker.sentence()
    schema = create_random_schema(faker)
    alertgroup = AlertGroupDetailedCreate(
        owner=user.email,
        tlp=tlp,
        view_count=view_count,
        first_view=first_view,
        message_id=message_id,
        subject=subject,
        back_refs=back_refs,
        alert_schema=schema,
    )
    alertgroup_in = crud.alert_group.create(db, obj_in=alertgroup)

    update_view_count = faker.pyint(0, 10)
    update_subject = faker.sentence()

    alertgroup_in_update = AlertGroupUpdate(
        view_count=update_view_count, subject=update_subject
    )
    crud.alert_group.update(db, db_obj=alertgroup_in, obj_in=alertgroup_in_update)
    alertgroup_2 = crud.alert_group.get(db, alertgroup_in.id)
    assert alertgroup_2
    assert alertgroup_2.view_count == update_view_count
    assert alertgroup_2.subject == update_subject


def test_delete_alertgroup(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    tlp = random.choice(list(TlpEnum))
    view_count = faker.pyint(0, 10)
    first_view = datetime.utcnow()
    message_id = str(faker.pyint(0, 10))
    subject = faker.sentence()
    back_refs = faker.sentence()
    schema = create_random_schema(faker)
    alertgroup = AlertGroupDetailedCreate(
        owner=user.email,
        tlp=tlp,
        view_count=view_count,
        first_view=first_view,
        message_id=message_id,
        subject=subject,
        back_refs=back_refs,
        alert_schema=schema,
    )
    alertgroup_in = crud.alert_group.create(db, obj_in=alertgroup)
    alertgroup_get = crud.alert_group.get(db, alertgroup_in.id)
    assert alertgroup_get == alertgroup_in
    crud.alert_group.remove(db, _id=alertgroup_in.id)
    alertgroup_get_delete = crud.alert_group.get(db, alertgroup_in.id)
    assert alertgroup_get_delete is None


def test_query_with_filters_alert(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alertgroups = []
    for _ in range(5):
        alertgroups.append(create_random_alertgroup_no_sig(db, faker, owner.username))

    random_alertgroup = random.choice(alertgroups)

    db_obj, count = crud.alert_group.query_with_filters(db, filter_dict={"id": random_alertgroup.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_alertgroup.id

    db_obj, count = crud.alert_group.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == count
    assert all(a.owner == random_alertgroup.owner for a in db_obj)

    db_obj, count = crud.alert_group.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == count - 1
    assert all(a.owner == random_alertgroup.owner for a in db_obj)

    db_obj, count = crud.alert_group.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == random_alertgroup.owner for a in db_obj)

    db_obj, count = crud.alert_group.query_with_filters(db, filter_dict={"owner": f"!{owner.username}"})

    assert db_obj is not None
    assert all(a.owner != random_alertgroup.owner for a in db_obj)

    db_obj, count = crud.alert_group.query_with_filters(db, filter_dict={"subject": f"!{random_alertgroup.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_alertgroup.subject for a in db_obj)
