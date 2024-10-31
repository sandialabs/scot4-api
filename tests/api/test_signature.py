import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum, EntryClassEnum
from app.core.config import settings

from tests.utils.signature import create_random_signature
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity
from tests.utils.entry import create_random_entry
from tests.utils.sigbody import create_random_sigbody
from tests.utils.link import create_link


def test_get_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/signature/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    signature_data = r.json()
    assert signature_data is not None
    assert signature_data["id"] == signature.id


def test_create_signature(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    data = {
        "owner": owner.username,
        "name": faker.word(),
        "description": faker.sentence(),
        "data": faker.json(),
        "type": faker.word()
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
    signature_data = r.json()
    assert signature_data is not None
    assert signature_data["id"] >= 1
    assert signature_data["name"] == data["name"]
    assert signature_data["type"] == data["type"]


def test_update_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)

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
    signature_data = r.json()
    assert signature_data is not None
    assert signature_data["id"] == signature.id
    assert signature_data["type"] == data["type"]
    assert signature_data["type"] != signature.type


def test_delete_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)

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
    signature_data = r.json()
    assert signature_data is not None
    assert signature_data["id"] == signature.id

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)

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
    signature_data = r.json()
    assert signature_data is not None
    assert signature_data["id"] == signature.id


def test_entries_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)
    entry = create_random_entry(db, faker, owner.username, target_type=TargetTypeEnum.signature, target_id=signature.id, entry_class=EntryClassEnum.entry)

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
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0
    assert len(entry_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id


def test_tag_untag_signature(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/signature/-1/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/tag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/tag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_signature = r.json()
    assert any([i for i in tag_signature["tags"] if i["id"] == tag.id])

    r = client.post(
        f"{settings.API_V1_STR}/signature/-1/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/untag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/untag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_signature = r.json()
    assert tag_signature["tags"] == []


def test_source_add_remove_signature(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/signature/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/add-source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_signature = r.json()
    assert any([i for i in source_signature["sources"] if i["id"] == source.id])

    r = client.post(
        f"{settings.API_V1_STR}/signature/-1/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/remove-source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/signature/{signature.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_signature = r.json()
    assert source_signature["sources"] == []


def test_entities_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)
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
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/entity",
        headers=superuser_token_headers
    )
    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_history_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)

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
    signature_data = r.json()
    assert any(i["audit_data"]["description"] == data["description"] for i in signature_data)
    assert signature_data[0]["audit_data"]["description"] == data["description"]

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
    signature_data = r.json()
    assert signature_data == []


def test_search_signatures(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    signatures = []
    for _ in range(5):
        signatures.append(create_random_signature(db, faker, owner.username))

    random_signature = random.choice(signatures)

    r = client.get(
        f"{settings.API_V1_STR}/signature/?id={random_signature.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    signature_search = r.json()
    assert signature_search is not None
    assert signature_search["result"] == []

    random_signature = random.choice(signatures)

    r = client.get(
        f"{settings.API_V1_STR}/signature/?id={random_signature.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    signature_search = r.json()
    assert signature_search is not None
    assert signature_search["totalCount"] == 1
    assert any(i["id"] == random_signature.id for i in signature_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/signature/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    signature_search = r.json()
    assert signature_search is not None
    assert signature_search["result"] == []

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
    signature = create_random_signature(db, faker,  owner.username, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

    name = r"((AAQ) Process [Executed] out of <drive>:\\ProgramData\\)"
    name2 = "((AAQ) Process [Executed] out of <drive>:\\ProgramData\\)"
    signature = create_random_signature(db, faker,  owner.username, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

    # test with a list, even though its bad will return something
    name = r"[(AAQ) Process [Executed] out of <drive>:\\ProgramData\\]"
    name2 = "[(AAQ) Process [Executed] out of <drive>:\\ProgramData\\]"
    signature = create_random_signature(db, faker,  owner.username, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] != signature.id for i in r.json()["result"])

    # test with a list, with escape characters
    name2 = "\\[(AAQ) Process [Executed] out of <drive>:\\ProgramData\\]"
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

    # test with bad negation with no escape characters shouldn't return anything
    name = r"!(AAQ) Process [Executed] out of <drive>:\\ProgramData\\"
    name2 = "!(AAQ) Process [Executed] out of <drive>:\\ProgramData\\"
    signature = create_random_signature(db, faker,  owner.username, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert all(i["id"] != signature.id for i in r.json()["result"])

    # test with bad negation with escape characters should return something
    name2 = "\\!(AAQ) Process [Executed] out of <drive>:\\ProgramData\\"
    signature = create_random_signature(db, faker,  owner.username, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

    # test with '+' special character
    name = r"(AAQ) Process Executed + out of <drive>:\\ProgramData\\"
    name2 = "(AAQ) Process Executed %2B out of <drive>:\\ProgramData\\"
    signature = create_random_signature(db, faker,  owner.username, name)
    r = client.get(
        f"{settings.API_V1_STR}/signature/?name={name2}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == signature.id for i in r.json()["result"])

def test_sigbodies_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)
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
    signature_data = r.json()
    assert signature_data == []

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/sigbodies",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    signature_data = r.json()
    assert signature_data is not None
    assert any(sigbody.id == i["id"] for i in signature_data)


def test_links_signature(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner.username)
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
    signature_data = r.json()
    assert signature_data is not None
    assert signature_data["totalCount"] == 0
    assert signature_data["resultCount"] == 0
    assert len(signature_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/signature/{signature.id}/links",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    signature_data = r.json()
    assert signature_data is not None
    assert signature_data["totalCount"] == 1
    assert signature_data["resultCount"] == 1
    assert signature_data["result"][0]["id"] == link.v1_id
