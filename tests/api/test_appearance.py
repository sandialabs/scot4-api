import random
from datetime import timezone

from urllib.parse import quote_plus
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from tests.utils.appearance import create_random_appearance


def test_create_appearance(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker) -> None:
    data = {"when_date": faker.iso8601(timezone.utc)}
    r = client.post(
        f"{settings.API_V1_STR}/appearance/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    created_appearance = r.json()
    assert created_appearance is not None
    assert created_appearance["when_date"].replace("Z", "+00:00") == data["when_date"]

    r = client.post(
        f"{settings.API_V1_STR}/appearance/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/appearance/",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422


def test_get_appearance(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    appearance = create_random_appearance(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/appearance/{appearance.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    created_appearance = r.json()
    assert created_appearance is not None
    assert created_appearance["id"] == appearance.id

    r = client.get(
        f"{settings.API_V1_STR}/appearance/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404


def test_search_appearance(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    appearances = []
    for _ in range(5):
        appearances.append(create_random_appearance(db, faker))

    # search for a random appearance
    random_appearance = random.choice(appearances)
    r = client.get(
        f"{settings.API_V1_STR}/appearance/?id={random_appearance.id}",
        headers=normal_user_token_headers,
    )
    searched_appearance = r.json()

    assert r.status_code == 200
    assert searched_appearance is not None
    assert searched_appearance["totalCount"] == 1
    assert searched_appearance["resultCount"] == 1

    r = client.get(
        f"{settings.API_V1_STR}/appearance/id=-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/appearance/?id={random_appearance.id}",
        headers=superuser_token_headers,
    )
    searched_appearance = r.json()

    assert r.status_code == 200
    assert searched_appearance is not None
    assert searched_appearance["totalCount"] == 1
    assert searched_appearance["resultCount"] == 1
    assert searched_appearance["result"][0]["id"] == random_appearance.id

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/appearance/?id=!{random_appearance.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_appearance = r.json()
    assert all(a["id"] != random_appearance.id for a in api_appearance["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/appearance/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/appearance/?id=({appearances[0].id},{appearances[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_appearance = r.json()
    assert api_appearance["result"][0]["id"] == appearances[0].id
    assert api_appearance["result"][3]["id"] == appearances[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/appearance/?id=!({appearances[0].id},{appearances[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_appearance = r.json()
    assert any(a["id"] != appearances[0].id for a in api_appearance["result"])
    assert any(a["id"] != appearances[1].id for a in api_appearance["result"])
    assert any(a["id"] != appearances[2].id for a in api_appearance["result"])
    assert any(a["id"] != appearances[3].id for a in api_appearance["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/appearance/?id=[{appearances[0].id},{appearances[4].id},{appearances[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_appearance = r.json()
    assert len(api_appearance["result"]) == 3
    assert api_appearance["result"][0]["id"] == appearances[0].id
    assert api_appearance["result"][1]["id"] == appearances[2].id
    assert api_appearance["result"][2]["id"] == appearances[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/appearance/?id=![{appearances[0].id},{appearances[4].id},{appearances[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_appearance = r.json()
    assert all(a["id"] != appearances[0].id for a in api_appearance["result"])
    assert all(a["id"] != appearances[2].id for a in api_appearance["result"])
    assert all(a["id"] != appearances[4].id for a in api_appearance["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/appearance/?when_date={quote_plus(random_appearance.when_date.isoformat())}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_appearance = r.json()
    assert any(i["id"] == random_appearance.id for i in api_appearance["result"])

    r = client.get(
        f"{settings.API_V1_STR}/appearance/?when_date={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/appearance/?value_str={random_appearance.value_str}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_appearance = r.json()
    assert any(i["id"] == random_appearance.id for i in api_appearance["result"])

    r = client.get(
        f"{settings.API_V1_STR}/appearance/?when_date={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/appearance/?target_type={random_appearance.target_type.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_appearance = r.json()
    assert all(i["target_type"] == random_appearance.target_type.name for i in api_appearance["result"])

    r = client.get(
        f"{settings.API_V1_STR}/appearance/?target_type={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422


def test_update_appearance(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    appearance = create_random_appearance(db, faker)

    data = {"when_date": faker.iso8601(timezone.utc)}
    r = client.put(
        f"{settings.API_V1_STR}/appearance/{appearance.id}",
        headers=superuser_token_headers,
        json=data,
    )
    updated_appearance = r.json()

    assert r.status_code == 200
    assert updated_appearance is not None
    assert updated_appearance["when_date"].replace("Z", "+00:00") != appearance.when_date
    assert updated_appearance["when_date"].replace("Z", "+00:00") == data["when_date"]

    r = client.put(
        f"{settings.API_V1_STR}/appearance/{appearance.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/appearance/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_delete_appearance(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    appearance = create_random_appearance(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/appearance/{appearance.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/appearance/{appearance.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    deleted_appearance = r.json()
    assert deleted_appearance is not None
    assert deleted_appearance["id"] == appearance.id

    r = client.get(
        f"{settings.API_V1_STR}/appearance/{appearance.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/appearance/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404
