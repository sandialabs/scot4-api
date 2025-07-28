import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.pivot import create_random_pivot
from tests.utils.entity_class import create_random_entity_class
from tests.utils.entity_type import create_random_entity_type


def test_get_pivot(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/pivot/{pivot.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert pivot_data["id"] == pivot.id

    r = client.get(
        f"{settings.API_V1_STR}/pivot/0",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_create_pivot(client: TestClient, normal_user_token_headers: dict, faker: Faker) -> None:
    pivot = {
        "title": faker.word(),
        "template": faker.word(),
        "description": faker.sentence()
    }

    r = client.post(
        f"{settings.API_V1_STR}/pivot",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/pivot",
        headers=normal_user_token_headers,
        json=pivot
    )

    assert 200 <= r.status_code < 300
    pivot_data = r.json()
    assert pivot_data is not None
    assert pivot_data["id"] > 0
    assert pivot_data["title"] == pivot["title"]


def test_create_pivots(client: TestClient, normal_user_token_headers: dict, faker: Faker) -> None:
    pivot = [{
        "title": faker.word(),
        "template": faker.word(),
        "description": faker.sentence()
    },{
        "title": faker.word(),
        "template": faker.word(),
        "description": faker.sentence()
    }]

    r = client.post(
        f"{settings.API_V1_STR}/pivot/many/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/pivot/many/",
        headers=normal_user_token_headers,
        json=pivot
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert len(pivot_data) == 2
    assert pivot_data[0]["id"] > 0
    assert pivot_data[0]["title"] == pivot[0]["title"]
    assert pivot_data[1]["id"] > 0
    assert pivot_data[1]["title"] == pivot[1]["title"]
    assert pivot_data[0]["id"] < pivot_data[1]["id"]


def test_update_pivot(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)

    data = {
        "template": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert pivot_data["id"] == pivot.id
    assert pivot_data["template"] == data["template"]

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/pivot/-1",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_update_pivots(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    pivot1 = create_random_pivot(db, faker)
    pivot2 = create_random_pivot(db, faker)

    data = {
        "template": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/pivot/many/?ids={pivot1.id}&ids={pivot2.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert len(pivot_data) == 2
    assert pivot_data[0]["id"] == pivot1.id
    assert pivot_data[0]["template"] == data["template"]
    assert pivot_data[1]["id"] == pivot2.id
    assert pivot_data[1]["template"] == data["template"]

    r = client.put(
        f"{settings.API_V1_STR}/pivot/many/?ids=-1",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_delete_pivot(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/pivot/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/pivot/{pivot.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert pivot_data["id"] == pivot.id

    r = client.get(
        f"{settings.API_V1_STR}/pivot/{pivot.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_delete_pivots(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    pivot1 = create_random_pivot(db, faker)
    pivot2 = create_random_pivot(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/pivot/many/?ids=-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/pivot/many/?ids={pivot1.id}&ids={pivot2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert len(pivot_data) == 2
    assert pivot_data[0]["id"] == pivot1.id
    assert pivot_data[1]["id"] == pivot2.id

    r = client.get(
        f"{settings.API_V1_STR}/pivot/{pivot1.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/pivot/{pivot2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_history_pivot(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)

    data = {
        "template": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/pivot/-1/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data == []

    r = client.get(
        f"{settings.API_V1_STR}/pivot/{pivot.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert any(i["audit_data"]["template"] == data["template"] for i in pivot_data)


def test_entity_class_pivot(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)
    entity_class = create_random_entity_class(db, faker)

    # Regular users can modify pivots (for now)
    # r = client.put(
    #     f"{settings.API_V1_STR}/pivot/{pivot.id}/entity_class",
    #     headers=normal_user_token_headers,
    #     json={"entity_classes":[entity_class.id]}
    # )

    # assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}/entity_class",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/pivot/-1/entity_class",
        headers=superuser_token_headers,
        json={"entity_classes": [entity_class.id]}
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}/entity_class",
        headers=superuser_token_headers,
        json={"entity_classes": [-1]}
    )

    assert r.status_code == 400

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}/entity_class",
        headers=superuser_token_headers,
        json={"entity_classes": [entity_class.id]}
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert pivot_data["id"] == pivot.id
    assert len(pivot_data["entity_classes"]) == 1
    assert pivot_data["entity_classes"][0]["id"] == entity_class.id


def test_entity_type_pivot(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)
    entity_type = create_random_entity_type(db, faker)

    # Regular users can modify pivots (for now)
    # r = client.put(
    #     f"{settings.API_V1_STR}/pivot/{pivot.id}/entity_type",
    #     headers=normal_user_token_headers,
    #     json={"entity_types":[entity_type.id]}
    # )

    # assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/pivot/-1/entity_type",
        headers=superuser_token_headers,
        json={"entity_types": [entity_type.id]}
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}/entity_type",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}/entity_type",
        headers=superuser_token_headers,
        json={"entity_types": [-1]}
    )

    assert r.status_code == 400

    r = client.put(
        f"{settings.API_V1_STR}/pivot/{pivot.id}/entity_type",
        headers=superuser_token_headers,
        json={"entity_types": [entity_type.id]}
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert pivot_data["id"] == pivot.id
    assert len(pivot_data["entity_types"]) == 1
    assert pivot_data["entity_types"][0]["id"] == entity_type.id


def test_search_pivots(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    pivots = []
    for _ in range(5):
        pivots.append(create_random_pivot(db, faker))

    random_pivot = random.choice(pivots)

    r = client.get(
        f"{settings.API_V1_STR}/pivot/?id={random_pivot.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert pivot_data["totalCount"] == 1
    assert pivot_data["resultCount"] == 1
    assert pivot_data["result"][0]["id"] == random_pivot.id

    r = client.get(
        f"{settings.API_V1_STR}/pivot/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    pivot_data = r.json()
    assert pivot_data is not None
    assert pivot_data["totalCount"] == 0
    assert pivot_data["resultCount"] == 0
    assert len(pivot_data["result"]) == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/pivot/?id=!{random_pivot.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_pivot.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/pivot/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/pivot/?id=({pivots[0].id},{pivots[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == pivots[0].id
    assert r.json()["result"][3]["id"] == pivots[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/pivot/?id=!({pivots[0].id},{pivots[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != pivots[0].id for a in r.json()["result"])
    assert any(a["id"] != pivots[1].id for a in r.json()["result"])
    assert any(a["id"] != pivots[2].id for a in r.json()["result"])
    assert any(a["id"] != pivots[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/pivot/?id=[{pivots[0].id},{pivots[4].id},{pivots[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == pivots[0].id
    assert r.json()["result"][1]["id"] == pivots[2].id
    assert r.json()["result"][2]["id"] == pivots[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/pivot/?id=![{pivots[0].id},{pivots[4].id},{pivots[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != pivots[0].id for a in r.json()["result"])
    assert all(a["id"] != pivots[2].id for a in r.json()["result"])
    assert all(a["id"] != pivots[4].id for a in r.json()["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/pivot/?title={random_pivot.title}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_pivot.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/pivot/?template={random_pivot.template}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_pivot.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/pivot/?description={random_pivot.description}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_pivot.id for i in r.json()["result"])
