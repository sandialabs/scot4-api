import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from tests.utils.entity_class import create_random_entity_class


def test_create_entity_class(client: TestClient, normal_user_token_headers: dict, faker: Faker) -> None:
    data = {
        "display_name": faker.word(),
        "name": f"{faker.word()}_{faker.pyint()}",
        "icon": faker.word(),
        "description": faker.sentence()
    }

    r = client.post(
        f"{settings.API_V1_STR}/entity_class",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    entity_class_data = r.json()
    assert entity_class_data is not None
    assert entity_class_data["id"] > 0
    assert entity_class_data["name"] == data["name"]

    r = client.post(
        f"{settings.API_V1_STR}/entity_class",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_entity_class(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity_class = create_random_entity_class(db, faker)

    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/entity_class/{entity_class.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    get_entity_class = r.json()
    assert get_entity_class is not None
    assert get_entity_class["id"] == entity_class.id
    assert get_entity_class["description"] == data["description"]

    r = client.put(
        f"{settings.API_V1_STR}/entity_class/-1",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/entity_class/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_get_entity_class(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    entity_class = create_random_entity_class(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/entity_class/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/entity_class/{entity_class.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entity_class_data = r.json()
    assert entity_class_data is not None
    assert entity_class_data["id"] == entity_class.id


def test_history_entity_class(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    entity_class = create_random_entity_class(db, faker)

    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/entity_class/{entity_class.id}",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/entity_class/{entity_class.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entity_class_data = r.json()
    assert any(i["audit_data"]["description"] == data["description"] for i in entity_class_data)
    assert entity_class_data[0]["audit_data"]["description"] == data["description"]

    r = client.get(
        f"{settings.API_V1_STR}/entity_class/-1/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    dispatch_data = r.json()
    assert len(dispatch_data) == 0


def test_search_entity_class(client: TestClient, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    entity_classes = []
    for _ in range(5):
        entity_classes.append(create_random_entity_class(db, faker))

    random_entity_class = random.choice(entity_classes)

    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?id={random_entity_class.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    entity_class_data = r.json()
    assert entity_class_data["totalCount"] == 1
    assert entity_class_data["resultCount"] == 1
    assert any(x["id"] == random_entity_class.id for x in entity_class_data["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    entity_class_data = r.json()
    assert entity_class_data["totalCount"] == 0
    assert entity_class_data["resultCount"] == 0
    assert len(entity_class_data["result"]) == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?id=!{random_entity_class.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert all(a["id"] != random_entity_class.id for a in api_dispatch["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?id=({entity_classes[0].id},{entity_classes[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert api_dispatch["result"][0]["id"] == entity_classes[0].id
    assert api_dispatch["result"][3]["id"] == entity_classes[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?id=!({entity_classes[0].id},{entity_classes[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert any(a["id"] != entity_classes[0].id for a in api_dispatch["result"])
    assert any(a["id"] != entity_classes[1].id for a in api_dispatch["result"])
    assert any(a["id"] != entity_classes[2].id for a in api_dispatch["result"])
    assert any(a["id"] != entity_classes[3].id for a in api_dispatch["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?id=[{entity_classes[0].id},{entity_classes[4].id},{entity_classes[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 3
    assert api_dispatch["result"][0]["id"] == entity_classes[0].id
    assert api_dispatch["result"][1]["id"] == entity_classes[2].id
    assert api_dispatch["result"][2]["id"] == entity_classes[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?id=![{entity_classes[0].id},{entity_classes[4].id},{entity_classes[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert all(a["id"] != entity_classes[0].id for a in api_dispatch["result"])
    assert all(a["id"] != entity_classes[2].id for a in api_dispatch["result"])
    assert all(a["id"] != entity_classes[4].id for a in api_dispatch["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?display_name={random_entity_class.display_name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entity_class.id for i in r.json()["result"])
    r = client.get(
        f"{settings.API_V1_STR}/entity_class/?icon={random_entity_class.icon}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entity_class.id for i in r.json()["result"])
