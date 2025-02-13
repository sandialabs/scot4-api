import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TargetTypeEnum
from tests.utils.signature import create_random_signature
from tests.utils.sigbody import create_random_sigbody
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source


def test_get_sigbody(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = create_random_sigbody(db, faker, signature.id)

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    sigbody_data = r.json()
    assert sigbody_data is not None
    assert sigbody_data["id"] == sigbody.id


def test_create_sigbody(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)

    data = {
        "revision": faker.pyint(),
        "body": faker.sentence(),
        "body64": faker.sentence(),
        "signature_id": signature.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/sigbody",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/sigbody",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    sigbody_data = r.json()
    assert sigbody_data is not None
    assert sigbody_data["id"] >= 1
    assert sigbody_data["body"] == data["body"]
    assert sigbody_data["body64"] == data["body64"]


def test_update_sigbody(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = create_random_sigbody(db, faker, signature.id)

    data = {
        "body": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/sigbody/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    sigbody_data = r.json()
    assert sigbody_data is not None
    assert sigbody_data["id"] == sigbody.id
    assert sigbody_data["body"] == data["body"]
    assert sigbody_data["body"] != sigbody.body


def test_delete_sigbody(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = create_random_sigbody(db, faker, signature.id)

    r = client.delete(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/sigbody/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    sigbody_data = r.json()
    assert sigbody_data is not None
    assert sigbody_data["id"] == sigbody.id

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_sigbody(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = create_random_sigbody(db, faker, signature.id)

    r = client.delete(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/undelete?target_id={sigbody.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/undelete?target_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/undelete?target_id={sigbody.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    sigbody_data = r.json()
    assert sigbody_data is not None
    assert sigbody_data["id"] == sigbody.id


def test_tag_untag_sigbody(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = create_random_sigbody(db, faker, signature.id)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/-1/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/tag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/tag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_sigbody = r.json()
    assert any([i for i in tag_sigbody["tags"] if i["id"] == tag.id])

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/-1/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/untag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/untag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_sigbody = r.json()
    assert tag_sigbody["tags"] == []


def test_source_add_remove_sigbody(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = create_random_sigbody(db, faker, signature.id)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/add-source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_sigbody = r.json()
    assert any([i for i in source_sigbody["sources"] if i["id"] == source.id])

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/-1/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/remove-source",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/sigbody/{sigbody.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_sigbody = r.json()
    assert source_sigbody["sources"] == []


def test_search_sigbody(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)

    sigbodies = []
    for _ in range(5):
        sigbodies.append(create_random_sigbody(db, faker, signature.id))

    random_sigbody = random.choice(sigbodies)

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id={random_sigbody.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    sigbody_search = r.json()
    assert sigbody_search is not None
    assert sigbody_search["result"] == []

    random_sigbody = random.choice(sigbodies)

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id={random_sigbody.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    sigbody_search = r.json()
    assert sigbody_search is not None
    assert sigbody_search["totalCount"] == 1
    assert any(i["id"] == random_sigbody.id for i in sigbody_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    sigbody_search = r.json()
    assert sigbody_search is not None
    assert sigbody_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id=!{random_sigbody.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_sigbody.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id=({sigbodies[0].id},{sigbodies[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == sigbodies[0].id
    assert r.json()["result"][3]["id"] == sigbodies[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id=!({sigbodies[0].id},{sigbodies[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != sigbodies[0].id for a in r.json()["result"])
    assert any(a["id"] != sigbodies[1].id for a in r.json()["result"])
    assert any(a["id"] != sigbodies[2].id for a in r.json()["result"])
    assert any(a["id"] != sigbodies[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id=[{sigbodies[0].id},{sigbodies[4].id},{sigbodies[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == sigbodies[0].id
    assert r.json()["result"][1]["id"] == sigbodies[2].id
    assert r.json()["result"][2]["id"] == sigbodies[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?id=![{sigbodies[0].id},{sigbodies[4].id},{sigbodies[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != sigbodies[0].id for a in r.json()["result"])
    assert all(a["id"] != sigbodies[2].id for a in r.json()["result"])
    assert all(a["id"] != sigbodies[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.sigbody, random_sigbody.id)

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_sigbody.id

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_sigbody.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.sigbody, random_sigbody.id)

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_sigbody.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/sigbody/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_sigbody.id for i in r.json()["result"])
