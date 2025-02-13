import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas import ApiKey
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user
from tests.utils.apikey import create_apikey


def test_create_alertgroup(db: Session, faker: Faker) -> None:
    key = faker.uuid4()
    user = create_random_user(db, faker)

    apikey = ApiKey(key=key, owner=user.email)
    apikey_in = crud.apikey.create(db, obj_in=apikey)

    assert apikey_in
    assert apikey_in.key == key
    assert apikey_in.owner == user.email


def test_create_alertgroup_with_roles(db: Session, faker: Faker) -> None:
    key = faker.uuid4()
    user = create_random_user(db, faker)

    apikey = ApiKey(key=key, owner=user.email)
    apikey_in = crud.apikey.create(db, obj_in=apikey)
    for _ in range(5):
        apikey_in.roles.append(create_random_role(db, faker))
    db.add(apikey_in)
    db.flush()

    assert apikey_in
    assert apikey_in.key == key
    assert apikey_in.owner == user.email


def test_get_apikey(db: Session, faker: Faker) -> None:
    key = faker.uuid4()
    user = create_random_user(db, faker)

    apikey = ApiKey(key=key, owner=user.email)
    apikey_in = crud.apikey.create(db, obj_in=apikey)
    apikey_get = crud.apikey.get(db, apikey_in.key)

    assert apikey_get
    assert apikey_in.owner == apikey_get.owner
    assert apikey_in.key == apikey_get.key


def test_update_apikey(db: Session, faker: Faker) -> None:
    key = faker.uuid4()
    user = create_random_user(db, faker)

    apikey = ApiKey(key=key, owner=user.email, active=True)
    apikey_in = crud.apikey.create(db, obj_in=apikey)
    update_dict = {"active": False}

    crud.apikey.update(db, db_obj=apikey_in, obj_in=update_dict)
    apikey_2 = crud.apikey.get(db, apikey_in.key)
    assert apikey_2
    assert apikey_2.key == key
    assert apikey_2.owner == user.email
    assert apikey_2.active is False


def test_delete_alertgroup(db: Session, faker: Faker) -> None:
    key = faker.uuid4()
    user = create_random_user(db, faker)

    apikey = ApiKey(key=key, owner=user.email)
    apikey_in = crud.apikey.create(db, obj_in=apikey)
    apikey_get = crud.apikey.get(db, apikey_in.key)
    assert apikey_get == apikey_in
    crud.apikey.remove(db, key=apikey_in.key)
    apikey_get_delete = crud.apikey.get(db, apikey_in.key)
    assert apikey_get_delete is None


def test_query_with_filters_alert(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    apikeys = []
    for _ in range(5):
        apikeys.append(create_apikey(db, faker, owner))

    random_apikey = random.choice(apikeys)

    db_obj, count = crud.apikey.query_with_filters(db, filter_dict={"key": random_apikey.key})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].key == random_apikey.key

    db_obj, count = crud.apikey.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == count
    assert all(a.owner == random_apikey.owner for a in db_obj)

    db_obj, count = crud.apikey.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == count - 1
    assert all(a.owner == random_apikey.owner for a in db_obj)

    db_obj, count = crud.apikey.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == random_apikey.owner for a in db_obj)

    db_obj, count = crud.apikey.query_with_filters(db, filter_dict={"key": f"!{random_apikey.key}"})

    assert db_obj is not None
    assert all(a.key != random_apikey.key for a in db_obj)
