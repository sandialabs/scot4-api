import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TargetTypeEnum
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.threat_model_item import create_random_threat_model_item


import pytest
pytest.skip("Threat model item api is currently disabled", allow_module_level=True)


def test_get_threat_model_item(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    threat_model_item_data = r.json()
    assert threat_model_item_data is not None
    assert threat_model_item_data["id"] == threat_model_item.id


def test_create_threat_model_item(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    data = {
        "title": faker.sentence(),
        "type": faker.word(),
        "description": faker.sentence(),
        "data": faker.json()
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    threat_model_item_data = r.json()
    assert threat_model_item_data is not None
    assert threat_model_item_data["id"] >= 1
    assert threat_model_item_data["title"] == data["title"]
    assert threat_model_item_data["type"] == data["type"]


def test_create_threat_model_items(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    data = [{
        "title": faker.sentence(),
        "type": faker.word(),
        "description": faker.sentence(),
        "data": faker.json()
    },{
        "title": faker.sentence(),
        "type": faker.word(),
        "description": faker.sentence(),
        "data": faker.json()
    }]

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/many",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/many",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    threat_model_item_data = r.json()
    assert threat_model_item_data is not None
    assert len(threat_model_item_data) == 2
    assert threat_model_item_data[0]["id"] >= 1
    assert threat_model_item_data[0]["title"] == data[0]["title"]
    assert threat_model_item_data[0]["type"] == data[0]["type"]
    assert threat_model_item_data[1]["id"] >= 1
    assert threat_model_item_data[1]["title"] == data[1]["title"]
    assert threat_model_item_data[1]["type"] == data[1]["type"]
    assert threat_model_item_data[0]["id"] < threat_model_item_data[1]["id"]


def test_update_threat_model_item(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker)

    data = {
        "title": faker.sentence(),
        "type": faker.word(),
        "description": faker.sentence(),
        "data": faker.json()
    }

    r = client.put(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/threat_model_item/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    threat_model_item_data = r.json()
    assert threat_model_item_data is not None
    assert threat_model_item_data["id"] == threat_model_item.id
    assert threat_model_item_data["type"] == data["type"]


def test_update_threat_model_items(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item1 = create_random_threat_model_item(db, faker)
    threat_model_item2 = create_random_threat_model_item(db, faker)

    data = {
        "title": faker.sentence(),
        "type": faker.word(),
        "description": faker.sentence(),
        "data": faker.json()
    }

    r = client.put(
        f"{settings.API_V1_STR}/threat_model_item/many/?ids={threat_model_item1.id}&ids={threat_model_item2.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/threat_model_item/many/?ids=-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/threat_model_item/many/?ids={threat_model_item1.id}&ids={threat_model_item2.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/threat_model_item/many/?ids={threat_model_item1.id}&ids={threat_model_item2.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    threat_model_item_data = r.json()
    assert threat_model_item_data is not None
    assert len(threat_model_item_data) == 2
    assert threat_model_item_data[0]["id"] == threat_model_item1.id
    assert threat_model_item_data[0]["type"] == data["type"]
    assert threat_model_item_data[1]["id"] == threat_model_item2.id
    assert threat_model_item_data[1]["type"] == data["type"]


def test_delete_threat_model_item(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/threat_model_item/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    threat_model_item_data = r.json()
    assert threat_model_item_data is not None
    assert threat_model_item_data["id"] == threat_model_item.id

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_delete_threat_model_items(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item1 = create_random_threat_model_item(db, faker)
    threat_model_item2 = create_random_threat_model_item(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/threat_model_item/many/?ids={threat_model_item1.id}&ids={threat_model_item2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/threat_model_item/many/?ids=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/threat_model_item/many/?ids={threat_model_item1.id}&ids={threat_model_item2.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    threat_model_item_data = r.json()
    assert threat_model_item_data is not None
    assert len(threat_model_item_data) == 2
    assert threat_model_item_data[0]["id"] == threat_model_item1.id
    assert threat_model_item_data[1]["id"] == threat_model_item2.id

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item1.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item2.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_tag_untag_threat_model_item(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/-1/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/tag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/tag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_threat_model_item = r.json()
    assert any([i for i in tag_threat_model_item["tags"] if i["id"] == tag.id])

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/-1/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/untag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/untag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_threat_model_item = r.json()
    assert tag_threat_model_item["tags"] == []


def test_source_add_remove_threat_model_item(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/add-source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_threat_model_item = r.json()
    assert any([i for i in source_threat_model_item["sources"] if i["id"] == source.id])

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/-1/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/remove-source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_threat_model_item = r.json()
    assert source_threat_model_item["sources"] == []


def test_search_threat_model_items(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_items = []
    for _ in range(5):
        threat_model_items.append(create_random_threat_model_item(db, faker))

    random_threat_model_item = random.choice(threat_model_items)

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id={random_threat_model_item.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    threat_model_item_search = r.json()
    assert threat_model_item_search is not None
    assert threat_model_item_search["result"] == []

    random_threat_model_item = random.choice(threat_model_items)

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id={random_threat_model_item.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    threat_model_item_search = r.json()
    assert threat_model_item_search is not None
    assert threat_model_item_search["totalCount"] == 1
    assert any(i["id"] == random_threat_model_item.id for i in threat_model_item_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    threat_model_item_search = r.json()
    assert threat_model_item_search is not None
    assert threat_model_item_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id=!{random_threat_model_item.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_threat_model_item.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id=({threat_model_items[0].id},{threat_model_items[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == threat_model_items[0].id
    assert r.json()["result"][3]["id"] == threat_model_items[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id=!({threat_model_items[0].id},{threat_model_items[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != threat_model_items[0].id for a in r.json()["result"])
    assert any(a["id"] != threat_model_items[1].id for a in r.json()["result"])
    assert any(a["id"] != threat_model_items[2].id for a in r.json()["result"])
    assert any(a["id"] != threat_model_items[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id=[{threat_model_items[0].id},{threat_model_items[4].id},{threat_model_items[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == threat_model_items[0].id
    assert r.json()["result"][1]["id"] == threat_model_items[2].id
    assert r.json()["result"][2]["id"] == threat_model_items[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id=![{threat_model_items[0].id},{threat_model_items[4].id},{threat_model_items[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != threat_model_items[0].id for a in r.json()["result"])
    assert all(a["id"] != threat_model_items[2].id for a in r.json()["result"])
    assert all(a["id"] != threat_model_items[4].id for a in r.json()["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?type={random_threat_model_item.type}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_threat_model_item.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?title={random_threat_model_item.title}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_threat_model_item.id for i in r.json()["result"])

    tag = create_random_tag(db, faker, TargetTypeEnum.threat_model_item, random_threat_model_item.id)

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_threat_model_item.id

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_threat_model_item.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.threat_model_item, random_threat_model_item.id)

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_threat_model_item.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_threat_model_item.id for i in r.json()["result"])
