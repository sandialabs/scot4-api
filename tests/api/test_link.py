import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TargetTypeEnum

from tests.utils.alert import create_random_alert
from tests.utils.link import create_random_link, get_type_object


def test_get_link(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    link = create_random_link(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/link/{link.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    link_data = r.json()
    assert link_data is not None
    assert link_data["id"] == link.id

    r = client.get(
        f"{settings.API_V1_STR}/link/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_create_link(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    v0_type, v0_id = get_type_object(db, faker)
    v1_type, v1_id = get_type_object(db, faker)

    data = {
        "v0_type": v0_type.value,
        "v0_id": v0_id,
        "v1_type": v1_type.value,
        "v1_id": v1_id
    }

    r = client.post(
        f"{settings.API_V1_STR}/link",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    link_data = r.json()
    assert link_data is not None
    assert link_data["id"] > 0
    assert link_data["v0_id"] == data["v0_id"]
    assert link_data["v1_id"] == data["v1_id"]

    r = client.post(
        f"{settings.API_V1_STR}/link",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422


def test_update_link(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    link = create_random_link(db, faker)

    data = {
        "context": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/link/{link.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    link_data = r.json()
    assert link_data is not None
    assert link_data["id"] == link.id
    assert link_data["context"] != link.context
    assert link_data["context"] == data["context"]

    r = client.put(
        f"{settings.API_V1_STR}/link/{link.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/link/-1",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_delete_link(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    link = create_random_link(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/link/{link.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    link_data = r.json()
    assert link_data is not None
    assert link_data["id"] == link.id

    r = client.get(
        f"{settings.API_V1_STR}/link/{link.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/link/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_search_link(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    links = []
    for _ in range(5):
        alert = create_random_alert(db, faker)
        links.append(create_random_link(db, faker, TargetTypeEnum.alert, alert.id))
    random_link = random.choice(links)

    r = client.get(
        f"{settings.API_V1_STR}/link/?v1_id={random_link.v1_id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    link_data = r.json()
    assert link_data is not None
    assert link_data["resultCount"] >= 1
    assert any(i["id"] == random_link.id for i in link_data["result"])

    r = client.get(
        f"{settings.API_V1_STR}/link/?v1_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    link_data = r.json()
    assert link_data is not None
    assert link_data["resultCount"] == 0
    assert len(link_data["result"]) == 0

    # int negations
    random_link = random.choice(links)
    r = client.get(
        f"{settings.API_V1_STR}/link/?v0_id=!{random_link.v0_id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_link = r.json()
    assert all(a["v0_id"] != random_link.v0_id for a in api_link["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/link/?v0_id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/link/?v0_id=({links[0].v0_id},{links[3].v0_id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_link = r.json()
    assert all(a["v0_id"] >= links[0].v0_id for a in api_link["result"])
    assert all(a["v0_id"] <= links[3].v0_id for a in api_link["result"])

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/link/?v0_id=!({links[0].v0_id},{links[3].v0_id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_link = r.json()
    assert any(a["v0_id"] != links[0].v0_id for a in api_link["result"])
    assert any(a["v0_id"] != links[1].v0_id for a in api_link["result"])
    assert any(a["v0_id"] != links[2].v0_id for a in api_link["result"])
    assert any(a["v0_id"] != links[3].v0_id for a in api_link["result"])


def test_delete_links_between_objects(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    link = create_random_link(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/link/deletebetween",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    data = {
        "v0_id": link.v0_id,
        "v0_type": link.v0_type.value,
        "v1_id": link.v1_id,
        "v1_type": link.v1_type.value
    }

    r = client.post(
        f"{settings.API_V1_STR}/link/deletebetween",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    link_data = r.json()
    assert link_data is not None
    assert any(i["id"] == link.id for i in link_data)

    r = client.get(
        f"{settings.API_V1_STR}/link/{link.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404
