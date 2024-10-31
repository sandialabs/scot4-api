import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.core.config import settings

from tests.utils.alert import create_random_alert
from tests.utils.source import create_random_source


def test_get_source(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/source/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/source/{source.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["id"] == source.id


def test_create_source(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    data = {
        "name": f"{faker.unique.word()}_{faker.pyint()}".lower(),
        "description": faker.sentence(),
    }

    r = client.post(
        f"{settings.API_V1_STR}/source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/source",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["id"] >= 1
    assert source_data["name"] == data["name"].lower()
    assert source_data["description"] == data["description"]


def test_update_source(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)

    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/source/-1",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/source/{source.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/source/{source.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["id"] == source.id
    assert source_data["description"] == data["description"]
    assert source_data["description"] != source.description


def test_delete_source(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/source/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/source/{source.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["id"] == source.id

    r = client.get(
        f"{settings.API_V1_STR}/source/{source.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_source(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/source/{source.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/source/undelete?target_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/source/undelete?target_id={source.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["id"] == source.id


def test_search_source(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    sources = []
    for _ in range(5):
        sources.append(create_random_source(db, faker))

    random_source = random.choice(sources)

    r = client.get(
        f"{settings.API_V1_STR}/source/?id={random_source.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    source_search = r.json()
    assert source_search is not None
    assert source_search["totalCount"] == 1
    assert any(i["id"] == random_source.id for i in source_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/source/?id=-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    source_search = r.json()
    assert source_search is not None
    assert source_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/source/?id=!{random_source.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_source.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/source/?id={faker.word()}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/source/?id=({sources[0].id},{sources[3].id})",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == sources[0].id
    assert r.json()["result"][3]["id"] == sources[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/source/?id=!({sources[0].id},{sources[3].id})",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != sources[0].id for a in r.json()["result"])
    assert any(a["id"] != sources[1].id for a in r.json()["result"])
    assert any(a["id"] != sources[2].id for a in r.json()["result"])
    assert any(a["id"] != sources[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/source/?id=[{sources[0].id},{sources[4].id},{sources[2].id}]",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == sources[0].id
    assert r.json()["result"][1]["id"] == sources[2].id
    assert r.json()["result"][2]["id"] == sources[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/source/?id=![{sources[0].id},{sources[4].id},{sources[2].id}]",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != sources[0].id for a in r.json()["result"])
    assert all(a["id"] != sources[2].id for a in r.json()["result"])
    assert all(a["id"] != sources[4].id for a in r.json()["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/source/?description={random_source.description[1:-1]}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_source.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/source/?name={random_source.name[1:-1]}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_source.id for i in r.json()["result"])


def test_add_source(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id,
        "source_name": faker.word().lower(),
        "source_description": faker.sentence()
    }

    r = client.post(
        f"{settings.API_V1_STR}/source/source_by_name",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/source/source_by_name",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/source/source_by_name",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["id"] >= 0
    assert source_data["name"] == data["source_name"]


def test_apply_source(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)
    alert = create_random_alert(db, faker)

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/source/{source.id}/assign",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/source/{source.id}/assign",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/source/-1/assign",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/source/{source.id}/assign",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["id"] == source.id


def test_remove_source(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    source = create_random_source(db, faker, TargetTypeEnum.alert, alert.id)

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/source/{source.id}/remove",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/source/{source.id}/remove",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/source/-1/remove",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/source/{source.id}/remove",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["id"] == source.id

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": -1
    }

    r = client.post(
        f"{settings.API_V1_STR}/source/{source.id}/remove",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_source_appearances(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    source = create_random_source(db, faker, TargetTypeEnum.alert, alert.id)

    r = client.get(
        f"{settings.API_V1_STR}/source/-1/appearance",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["totalCount"] == 0
    assert source_data["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/source/{source.id}/appearance",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["totalCount"] == 0
    assert source_data["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/source/{source.id}/appearance",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    source_data = r.json()
    assert source_data is not None
    assert source_data["totalCount"] == 0
    assert source_data["resultCount"] == 0
