import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest

from app.enums import TargetTypeEnum, EntryClassEnum, ThreatModelName
from app.core.config import settings

from tests.utils.signature import create_random_signature
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity
from tests.utils.entry import create_random_entry
from tests.utils.sigbody import create_random_sigbody
from tests.utils.link import create_link
from tests.utils.threat_model_item import create_random_threat_model_item


def test_get_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/signature/0",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == signature.id


def test_create_signature(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    threat_model_item = create_random_threat_model_item(db, faker)
    data = {
        "owner": owner.username,
        "name": faker.word(),
        "description": faker.sentence(),
        "data": faker.json(),
        "type": faker.word(),
        "threat_model_items": [threat_model_item.id]
    }

    r = client.post(
        f"{settings.API_V1_STR}/signature",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] >= 1
    assert r.json()["name"] == data["name"]
    assert r.json()["type"] == data["type"]


def test_create_signatures(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    data = [{
        "owner": owner.username,
        "name": faker.word(),
        "description": faker.sentence(),
        "data": faker.json(),
        "type": faker.word()
    },{
        "owner": owner.username,
        "name": faker.word(),
        "description": faker.sentence(),
        "data": faker.json(),
        "type": faker.word()
    }]

    r = client.post(
        f"{settings.API_V1_STR}/signature/many",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/many",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert len(r.json()) == 2
    assert r.json()[0]["id"] >= 1
    assert r.json()[0]["name"] == data[0]["name"]
    assert r.json()[0]["type"] == data[0]["type"]
    assert r.json()[1]["id"] >= 1
    assert r.json()[1]["name"] == data[1]["name"]
    assert r.json()[1]["type"] == data[1]["type"]
    assert r.json()[0]["id"] < r.json()[1]["id"]


def test_update_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)

    data = {
        "type": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/signature/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == signature.id
    assert r.json()["type"] == data["type"]
    assert r.json()["type"] != signature.type


def test_update_signatures(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature1 = create_random_signature(db, faker, owner)
    signature2 = create_random_signature(db, faker, owner)

    data = {
        "type": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/signature/many/?ids={signature1.id}&ids={signature2.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/signature/many/?ids=-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/signature/many/?ids={signature1.id}&ids={signature2.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/signature/many/?ids={signature1.id}&ids={signature2.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert len(r.json()) == 2
    assert r.json()[0]["id"] == signature1.id
    assert r.json()[0]["type"] == data["type"]
    assert r.json()[1]["id"] == signature2.id
    assert r.json()[1]["type"] == data["type"]


def test_delete_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)

    r = client.delete(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/signature/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == signature.id

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_delete_signatures(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature1 = create_random_signature(db, faker, owner)
    signature2 = create_random_signature(db, faker, owner)

    r = client.delete(
        f"{settings.API_V1_STR}/signature/many/?ids={signature1.id}&ids={signature2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/signature/many/?ids=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/signature/many/?ids={signature1.id}&ids={signature2.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert len(r.json()) == 2
    assert r.json()[0]["id"] == signature1.id
    assert r.json()[1]["id"] == signature2.id

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature1.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature2.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)

    r = client.delete(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/signature/undelete?target_id={signature.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/undelete?target_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/undelete?target_id={signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == signature.id


def test_entries_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    entry = create_random_entry(db, faker, owner, target_type=TargetTypeEnum.signature, target_id=signature.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/signature/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["resultCount"] == 0
    assert r.json()["totalCount"] == 0
    assert len(r.json()["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["resultCount"] == 1
    assert r.json()["totalCount"] == 1
    assert r.json()["result"][0]["id"] == entry.id


def test_tag_untag_signature(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/signature/-1/tag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/tag",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/tag",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    assert any([i for i in r.json()["tags"] if i["id"] == tag.id])

    r = client.post(
        f"{settings.API_V1_STR}/signature/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/untag",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/untag",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    assert r.json()["tags"] == []


def test_source_add_remove_signature(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/signature/-1/add-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/add-source",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/add-source",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    assert any([i for i in r.json()["sources"] if i["id"] == source.id])

    r = client.post(
        f"{settings.API_V1_STR}/signature/-1/remove-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/remove-source",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    assert r.json()["sources"] == []


def test_entities_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    entity = create_random_entity(db, faker, TargetTypeEnum.signature, signature.id)

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/entity",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/signature/-1/entity",
        headers=superuser_token_headers
    )
    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["resultCount"] == 0
    assert r.json()["totalCount"] == 0
    assert len(r.json()["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/entity",
        headers=superuser_token_headers
    )
    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["resultCount"] == 1
    assert r.json()["totalCount"] == 1
    assert r.json()["result"][0]["id"] == entity.id


def test_history_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)

    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["audit_data"]["description"] == data["description"] for i in r.json())
    assert r.json()[0]["audit_data"]["description"] == data["description"]

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/history",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/signature/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() == []


def test_search_signatures(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    signatures = []
    for _ in range(5):
        signatures.append(create_random_signature(db, faker, owner))

    random_signature = random.choice(signatures)

    r = client.get(
        f"{settings.API_V1_STR}/signature/?id={random_signature.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["result"] == []

    random_signature = random.choice(signatures)

    r = client.get(
        f"{settings.API_V1_STR}/signature/?id={random_signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["totalCount"] == 1
    assert any(i["id"] == random_signature.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/signature/?id=!{random_signature.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_signature.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/signature/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/signature/?id=({signatures[0].id},{signatures[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == signatures[0].id
    assert r.json()["result"][3]["id"] == signatures[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/signature/?id=!({signatures[0].id},{signatures[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != signatures[0].id for a in r.json()["result"])
    assert any(a["id"] != signatures[1].id for a in r.json()["result"])
    assert any(a["id"] != signatures[2].id for a in r.json()["result"])
    assert any(a["id"] != signatures[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/signature/?id=[{signatures[0].id},{signatures[4].id},{signatures[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == signatures[0].id
    assert r.json()["result"][1]["id"] == signatures[2].id
    assert r.json()["result"][2]["id"] == signatures[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/signature/?id=![{signatures[0].id},{signatures[4].id},{signatures[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != signatures[0].id for a in r.json()["result"])
    assert all(a["id"] != signatures[2].id for a in r.json()["result"])
    assert all(a["id"] != signatures[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.signature, random_signature.id)

    r = client.get(
        f"{settings.API_V1_STR}/signature/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_signature.id

    r = client.get(
        f"{settings.API_V1_STR}/signature/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_signature.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.signature, random_signature.id)

    r = client.get(
        f"{settings.API_V1_STR}/signature/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_signature.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_signature.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={random_signature.name[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_signature.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?description={random_signature.description[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_signature.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?type={random_signature.type}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_signature.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?owner={random_signature.owner}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_signature.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?tlp={random_signature.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_signature.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/signature/?signature_group={random_signature.data['signature_group'][0]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_signature.id for i in r.json()["result"])

    # test with special characters should search normally
    name = r"(AAQ) Process [Executed] out of <drive>:\\ProgramData\\"
    name2 = "(AAQ) Process [Executed] out of <drive>:\\ProgramData\\"
    signature = create_random_signature(db, faker, owner, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

    name = r"((AAQ) Process [Executed] out of <drive>:\\ProgramData\\)"
    name2 = "((AAQ) Process [Executed] out of <drive>:\\ProgramData\\)"
    signature = create_random_signature(db, faker, owner, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

    # test with a list, with escape characters
    name = r"[(AAQ) Process [Executed] out of <drive>:\\ProgramData\\]"
    name2 = "\\[(AAQ) Process [Executed] out of <drive>:\\ProgramData\\]"
    signature = create_random_signature(db, faker, owner, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

    # test with bad negation with no escape characters shouldn't return anything
    name = r"!(AAQ) Process [Executed] out of <drive>:\\ProgramData\\"
    name2 = "!(AAQ) Process [Executed] out of <drive>:\\ProgramData\\"
    signature = create_random_signature(db, faker, owner, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert all(i["id"] != signature.id for i in r.json()["result"])

    # test with bad negation with escape characters should return something
    name2 = "\\!(AAQ) Process [Executed] out of <drive>:\\ProgramData\\"
    signature = create_random_signature(db, faker, owner, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

    # test with '+' special character
    name = r"(AAQ) Process Executed + out of <drive>:\\ProgramData\\"
    name2 = "(AAQ) Process Executed %2B out of <drive>:\\ProgramData\\"
    signature = create_random_signature(db, faker, owner, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])


@pytest.mark.skip("Sigbody api is disabled")
def test_sigbodies_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = create_random_sigbody(db, faker, signature.id)

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/sigbodies",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/signature/-1/sigbodies",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() == []

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/sigbodies",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert any(sigbody.id == i["id"] for i in r.json())


def test_links_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    link = create_link(db, faker, TargetTypeEnum.alert, None, TargetTypeEnum.signature, signature.id)

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/links",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/signature/-1/links",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["totalCount"] == 0
    assert r.json()["resultCount"] == 0
    assert len(r.json()["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/links",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["totalCount"] == 1
    assert r.json()["resultCount"] == 1
    assert r.json()["result"][0]["id"] == link.v1_id


def test_attack_navigator_signatures(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    signatures = []
    for _ in range(5):
        threat_model_item = create_random_threat_model_item(db, faker, ThreatModelName.attack, owner, False)
        signatures.append(create_random_signature(db, faker, owner, None, [threat_model_item]))

    random_signature = random.choice(signatures)

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id={random_signature.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert isinstance(r.json(), dict)
    assert "techniques" in r.json().keys()
    assert len(r.json()["techniques"]) == 0

    random_signature = random.choice(signatures)

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id={random_signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert isinstance(r.json(), dict)
    assert "techniques" in r.json().keys()
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1
    assert r.json()["techniques"][0]["links"][0]["label"] == f"SCOT Signature {random_signature.id}"

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert "techniques" in r.json().keys()
    assert len(r.json()["techniques"]) == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id=!{random_signature.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert isinstance(r.json(), dict)
    assert "techniques" in r.json().keys()
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {random_signature.id}" not in link_labels

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id=({signatures[0].id},{signatures[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {signatures[0].id}" in link_labels
    assert f"SCOT Signature {signatures[1].id}" in link_labels
    assert f"SCOT Signature {signatures[2].id}" in link_labels
    assert f"SCOT Signature {signatures[3].id}" in link_labels

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id=!({signatures[0].id},{signatures[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {signatures[0].id}" not in link_labels
    assert f"SCOT Signature {signatures[1].id}" not in link_labels
    assert f"SCOT Signature {signatures[2].id}" not in link_labels
    assert f"SCOT Signature {signatures[3].id}" not in link_labels
    assert f"SCOT Signature {signatures[4].id}" in link_labels

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id=[{signatures[0].id},{signatures[4].id},{signatures[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {signatures[0].id}" in link_labels
    assert f"SCOT Signature {signatures[1].id}" not in link_labels
    assert f"SCOT Signature {signatures[2].id}" in link_labels
    assert f"SCOT Signature {signatures[3].id}" not in link_labels
    assert f"SCOT Signature {signatures[4].id}" in link_labels

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?id=![{signatures[0].id},{signatures[4].id},{signatures[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {signatures[0].id}" not in link_labels
    assert f"SCOT Signature {signatures[1].id}" in link_labels
    assert f"SCOT Signature {signatures[2].id}" not in link_labels
    assert f"SCOT Signature {signatures[3].id}" in link_labels
    assert f"SCOT Signature {signatures[4].id}" not in link_labels

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.signature, random_signature.id)

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {random_signature.id}" in link_labels

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?name={random_signature.name[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {random_signature.id}" in link_labels

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?description={random_signature.description[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {random_signature.id}" in link_labels

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?type={random_signature.type}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {random_signature.id}" in link_labels

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?owner={random_signature.owner}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {random_signature.id}" in link_labels

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?tlp={random_signature.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {random_signature.id}" in link_labels

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/signature/attack_navigator/?signature_group={random_signature.data['signature_group'][0]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["techniques"]) >= 1
    assert len(r.json()["techniques"][0]["links"]) >= 1

    link_labels = []
    for technique in r.json()["techniques"]:
        for link in technique["links"]:
            link_labels.append(link["label"])

    assert f"SCOT Signature {random_signature.id}" in link_labels
