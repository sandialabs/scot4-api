import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TargetTypeEnum, ThreatModelName
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.threat_model_item import create_random_threat_model_item, create_random_threat_model_data
from tests.utils.user import create_random_user


def test_get_threat_model_item(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker, create_extras=False)

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/0",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == threat_model_item.id


def test_create_threat_model_item(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    threat_model_name = random.choice(list(ThreatModelName))
    threat_model_id, model_data = create_random_threat_model_data(faker, threat_model_name)
    
    data = {
        "threat_model_name": threat_model_name.value,
        "threat_model_id": threat_model_id,
        "data": model_data,
        "owner": owner.username
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
    assert r.json() is not None
    assert r.json()["id"] >= 1
    assert r.json()["threat_model_name"] == data["threat_model_name"]
    assert r.json()["threat_model_id"] == data["threat_model_id"]

    threat_model_id, model_data = create_random_threat_model_data(faker, ThreatModelName.attack)
    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": faker.word(),
        "data": {}
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, threat_model_id is not valid must be of format T1234 or T1234.123"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            f"{faker.word()}_{faker.pyint()}": faker.word()
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, url was not provided in data"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": 0
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, url needs to be a string"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": ""
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, url must be set"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": faker.word(),
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, version was not provided in data"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": faker.word(),
            "version": ""
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, version must be set"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": faker.word(),
            "version": faker.word()
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, version is not valid format"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": faker.word(),
            "version": f"{faker.pyint(1,10)}.{faker.pyint(0, 10)}"
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, tactics was not provided in data"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": faker.word(),
            "version": f"{faker.pyint(1,10)}.{faker.pyint(0, 10)}",
            "tactics": faker.pyint()
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, tactics needs to be a list of strings"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": faker.word(),
            "version": f"{faker.pyint(1,10)}.{faker.pyint(0, 10)}",
            "tactics": []
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, tactics must be set"

    data = {
        "threat_model_name": ThreatModelName.attack.value,
        "threat_model_id": threat_model_id,
        "data": {
            "url": faker.word(),
            "version": f"{faker.pyint(1,10)}.{faker.pyint(0, 10)}",
            "tactics": [faker.pyint()]
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 422
    assert r.json() is not None
    assert r.json()["detail"][0]["msg"] == "Value error, tactics needs to be a list of strings"


def test_many_create_threat_model_items(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    threat_model_name1 = random.choice(list(ThreatModelName))
    threat_model_id1, model_data1 = create_random_threat_model_data(faker, threat_model_name1)
    threat_model_name2 = random.choice(list(ThreatModelName))
    threat_model_id2, model_data2 = create_random_threat_model_data(faker, threat_model_name2)

    data = [{
        "threat_model_name": threat_model_name1.value,
        "threat_model_id": threat_model_id1,
        "data": model_data1,
        "owner": owner.username,
    },{
        "threat_model_name": threat_model_name2.value,
        "threat_model_id": threat_model_id2,
        "data": model_data2,
        "owner": owner.username,
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
    assert r.json() is not None
    assert len(r.json()) == 2
    assert r.json()[0]["id"] >= 1
    assert r.json()[0]["threat_model_name"] == data[0]["threat_model_name"]
    assert r.json()[0]["threat_model_id"] == data[0]["threat_model_id"]
    assert r.json()[1]["id"] == r.json()[0]["id"] + 1
    assert r.json()[1]["threat_model_name"] == data[1]["threat_model_name"]
    assert r.json()[1]["threat_model_id"] == data[1]["threat_model_id"]


def test_update_threat_model_item(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker, create_extras=False)
    threat_model_id, model_data = create_random_threat_model_data(faker, threat_model_item.threat_model_name)

    data = {
        "threat_model_id": threat_model_id,
        "data": model_data
    }

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
    assert r.json() is not None
    assert r.json()["id"] == threat_model_item.id
    assert r.json()["threat_model_id"] == data["threat_model_id"]
    assert r.json()["data"] == data["data"]


def test_update_many_threat_model_items(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item1 = create_random_threat_model_item(db, faker, create_extras=False)
    threat_model_item2 = create_random_threat_model_item(db, faker, create_extras=False)
    threat_model_id, model_data = create_random_threat_model_data(faker, threat_model_item1.threat_model_name)

    data = {
        "threat_model_id": threat_model_id,
        "data": model_data
    }

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

    print(r.json())
    assert r.status_code == 200
    assert r.json() is not None
    assert len(r.json()) == 2
    assert r.json()[0]["id"] == threat_model_item1.id
    assert r.json()[0]["threat_model_id"] == data["threat_model_id"]
    assert r.json()[1]["id"] == threat_model_item2.id
    assert r.json()[1]["threat_model_id"] == data["threat_model_id"]


def test_delete_threat_model_item(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker, create_extras=False)

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
    assert r.json() is not None
    assert r.json()["id"] == threat_model_item.id

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_many_delete_threat_model_items(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item1 = create_random_threat_model_item(db, faker, create_extras=False)
    threat_model_item2 = create_random_threat_model_item(db, faker, create_extras=False)

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
    assert r.json() is not None
    assert len(r.json()) == 2
    assert r.json()[0]["id"] == threat_model_item1.id
    assert r.json()[1]["id"] == threat_model_item2.id

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


def test_tag_untag_threat_model_item(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker, create_extras=False)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/-1/tag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/tag",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/tag",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    assert any([i for i in r.json()["tags"] if i["id"] == tag.id])

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/untag",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/untag",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    assert r.json()["tags"] == []


def test_source_add_remove_threat_model_item(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_item = create_random_threat_model_item(db, faker, create_extras=False)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/-1/add-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/add-source",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/add-source",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_threat_model_item = r.json()
    assert any([i for i in source_threat_model_item["sources"] if i["id"] == source.id])

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/-1/remove-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/remove-source",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/threat_model_item/{threat_model_item.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_threat_model_item = r.json()
    assert source_threat_model_item["sources"] == []


def test_search_threat_model_items(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    threat_model_items = []
    for _ in range(5):
        threat_model_items.append(create_random_threat_model_item(db, faker, create_extras=False))

    random_threat_model_item = random.choice(threat_model_items)

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?id={random_threat_model_item.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    threat_model_item_search = r.json()
    assert threat_model_item_search is not None
    assert threat_model_item_search["totalCount"] == 1
    assert any(i["id"] == random_threat_model_item.id for i in threat_model_item_search["result"])

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

    # threat_model_name checking
    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?threat_model_name={random_threat_model_item.threat_model_name.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["threat_model_name"] == random_threat_model_item.threat_model_name.value for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/threat_model_item/?threat_model_id={random_threat_model_item.threat_model_id}",
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
