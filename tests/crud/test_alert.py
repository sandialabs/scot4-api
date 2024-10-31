import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import StatusEnum, TlpEnum
from app.schemas.alert import AlertCreate, AlertUpdate
from tests.utils.user import create_random_user
from tests.utils.alert import create_random_alert


def test_create_alert(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    tlp = random.choice(list(TlpEnum))
    status = random.choice(list(StatusEnum))
    parsed = faker.pybool()
    alert_in = AlertCreate(owner=user.email, tlp=tlp, status=status, parsed=parsed)

    alert = crud.alert.create(db, obj_in=alert_in)
    assert alert.owner == user.email
    assert alert.tlp == tlp
    assert alert.status == status
    assert alert.parsed == parsed


def test_get_alert(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    tlp = random.choice(list(TlpEnum))
    status = random.choice(list(StatusEnum))
    parsed = faker.pybool()
    alert_in = AlertCreate(owner=user.email, tlp=tlp, status=status, parsed=parsed)

    alert = crud.alert.create(db, obj_in=alert_in)
    alert_2 = crud.alert.get(db, alert.id)
    assert alert.owner == alert_2.owner
    assert alert.tlp == alert_2.tlp
    assert alert.status == alert_2.status
    assert alert.parsed == alert_2.parsed


def test_update_alert(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    tlp = random.choice(list(TlpEnum))
    status = random.choice(list(StatusEnum))
    parsed = faker.pybool()
    alert_in = AlertCreate(owner=user.email, tlp=tlp, status=status, parsed=parsed)

    alert = crud.alert.create(db, obj_in=alert_in)
    update_status = random.choice(list(StatusEnum))
    update_parsed = faker.pybool()

    alert_in_update = AlertUpdate(status=update_status, parsed=update_parsed)
    crud.alert.update(db, db_obj=alert, obj_in=alert_in_update)
    alert_2 = crud.alert.get(db, alert.id)
    assert alert_2
    assert alert_2.status == update_status
    assert alert_2.parsed == update_parsed


def test_delete_alert(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    tlp = random.choice(list(TlpEnum))
    status = random.choice(list(StatusEnum))
    parsed = faker.pybool()
    alert_in = AlertCreate(owner=user.email, tlp=tlp, status=status, parsed=parsed)

    alert = crud.alert.create(db, obj_in=alert_in)
    alert_get = crud.alert.get(db, alert.id)
    assert alert_get == alert
    crud.alert.remove(db, _id=alert.id)
    alert_get_delete = crud.alert.get(db, alert.id)
    assert alert_get_delete is None


def test_query_with_filters_alert(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alert = []
    for _ in range(5):
        alert.append(create_random_alert(db, faker, owner.username))

    random_alert = random.choice(alert)

    db_obj, count = crud.alert.query_with_filters(db, filter_dict={"id": random_alert.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_alert.id

    db_obj, count = crud.alert.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == count
    assert all(a.owner == random_alert.owner for a in db_obj)

    db_obj, count = crud.alert.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == count - 1
    assert all(a.owner == random_alert.owner for a in db_obj)

    db_obj, count = crud.alert.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == random_alert.owner for a in db_obj)

    db_obj, count = crud.alert.query_with_filters(db, filter_dict={"owner": f"!{owner.username}"})

    assert db_obj is not None
    assert all(a.owner != random_alert.owner for a in db_obj)
