import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.enums import EntityTypeStatusEnum
from tests.utils.entity_type import create_random_entity_type


def test_create_entity_type(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    data = {
        "name": f"{faker.unique.word()}_{faker.pyint()}",
        "match_order": faker.pyint(1, 20),
        "status": random.choice(list(EntityTypeStatusEnum)).value,
        "match": faker.word(),
        "entity_type_data_ver": str(faker.pyfloat(1, 1, True)),
    }

    r = client.post(
        f"{settings.API_V1_STR}/entity_type/",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_entity_type = r.json()
    assert created_entity_type is not None
    assert created_entity_type["name"] == data["name"]
    assert created_entity_type["entity_type_data_ver"] == data["entity_type_data_ver"]
    assert crud.entity_type.get(db, created_entity_type["id"]) is not None

    r = client.post(
        f"{settings.API_V1_STR}/entity_type/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_entity_type(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    entity_type = create_random_entity_type(db, faker)
    data = {
        "name": f"{faker.unique.word()}_{faker.pyint()}"
    }

    r = client.put(
        f"{settings.API_V1_STR}/entity_type/{entity_type.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200

    r = client.put(
        f"{settings.API_V1_STR}/entity_type/{entity_type.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    put_entity_type = r.json()
    assert put_entity_type is not None
    assert put_entity_type["id"] == entity_type.id
    assert put_entity_type["name"] == data["name"]

    r = client.put(
        f"{settings.API_V1_STR}/entity_type/{entity_type.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/entity_type/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_get_entity_type(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    entity_type = create_random_entity_type(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/entity_type/{entity_type.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_type_get = r.json()
    assert entity_type.id == entity_type_get["id"]

    r = client.get(
        f"{settings.API_V1_STR}/entity_type/{entity_type.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/entity_type/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_search_entity_type(client: TestClient, superuser_token_headers: dict, faker: Faker, db: Session) -> None:

    entity_types = []
    for _ in range(5):
        entity_types.append(create_random_entity_type(db, faker))

    random_entity_type = random.choice(entity_types)

    r = client.get(
        f"{settings.API_V1_STR}/entity_type/?id={random_entity_type.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    entity_type_data = r.json()
    assert entity_type_data["totalCount"] == 1
    assert entity_type_data["resultCount"] == 1
    assert any(x["id"] == random_entity_type.id for x in entity_type_data["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entity_type/?id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    entity_type_data = r.json()
    assert entity_type_data["totalCount"] == 0
    assert entity_type_data["resultCount"] == 0
    assert len(entity_type_data["result"]) == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/entity_type/?id=!{random_entity_type.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_entity_type.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/entity_type/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/entity_type/?id=({entity_types[0].id},{entity_types[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == entity_types[0].id
    assert r.json()["result"][3]["id"] == entity_types[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/entity_type/?id=!({entity_types[0].id},{entity_types[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != entity_types[0].id for a in r.json()["result"])
    assert any(a["id"] != entity_types[1].id for a in r.json()["result"])
    assert any(a["id"] != entity_types[2].id for a in r.json()["result"])
    assert any(a["id"] != entity_types[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/entity_type/?id=[{entity_types[0].id},{entity_types[4].id},{entity_types[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == entity_types[0].id
    assert r.json()["result"][1]["id"] == entity_types[2].id
    assert r.json()["result"][2]["id"] == entity_types[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/entity_type/?id=![{entity_types[0].id},{entity_types[4].id},{entity_types[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != entity_types[0].id for a in r.json()["result"])
    assert all(a["id"] != entity_types[2].id for a in r.json()["result"])
    assert all(a["id"] != entity_types[4].id for a in r.json()["result"])
