import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TlpEnum, GuideStatusEnum, TargetTypeEnum, EntryClassEnum

from tests.utils.user import create_random_user
from tests.utils.guide import create_random_guide
from tests.utils.signature import create_random_signature
from tests.utils.entity import create_random_entity
from tests.utils.entry import create_random_entry


def test_get_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user)
    guide = create_random_guide(db, faker, user, signature)

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/guide/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    guide_get = r.json()
    assert guide_get is not None
    assert guide_get["id"] == guide.id


def test_create_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user)

    data = {
        "owner": user.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "subject": f"Guide for {signature.name}",
        "status": random.choice(list(GuideStatusEnum)).value
    }

    r = client.post(
        f"{settings.API_V1_STR}/guide",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    guide_create = r.json()
    assert guide_create is not None
    assert guide_create["id"] > 0
    assert guide_create["owner"] == data["owner"]
    assert guide_create["subject"] == data["subject"]

    r = client.post(
        f"{settings.API_V1_STR}/guide",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user)
    guide = create_random_guide(db, faker, user, signature, False)

    data = {
        "subject": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/guide/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    guide_update = r.json()
    assert guide_update is not None
    assert guide_update["id"] == guide.id
    assert guide_update["subject"] == data["subject"]
    assert guide_update["subject"] != guide.subject


def test_delete_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user)
    guide = create_random_guide(db, faker, user, signature, False)

    r = client.delete(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/guide/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    guide_update = r.json()
    assert guide_update is not None
    assert guide_update["id"] == guide.id

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_undelete_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user)
    guide = create_random_guide(db, faker, user, signature, False)

    r = client.delete(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/guide/undelete?target_id={guide.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/guide/undelete?target_id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/guide/undelete?target_id={guide.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    guide_undeleted = r.json()
    assert guide_undeleted is not None
    assert guide_undeleted["subject"] == guide.subject

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide_undeleted['id']}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    guide_get = r.json()
    assert guide_get is not None
    assert guide_undeleted["id"] == guide_get["id"]


def test_entries_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    guide = create_random_guide(db, faker, owner, signature, False)
    entry = create_random_entry(db, faker, owner, target_type=TargetTypeEnum.guide, target_id=guide.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/guide/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0
    assert len(entry_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id


def test_entities_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    guide = create_random_guide(db, faker, owner, signature, False)
    entity = create_random_entity(db, faker, TargetTypeEnum.guide, guide.id)

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}/entity",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/guide/-1/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_history_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user)
    guide = create_random_guide(db, faker, user, signature, False)

    data = {
        "subject": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/guide/{guide.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    guide_history = r.json()
    assert guide_history is not None
    assert any(i["audit_data"]["subject"] == data["subject"] for i in guide_history)

    r = client.get(
        f"{settings.API_V1_STR}/guide/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    guide_history = r.json()
    assert guide_history is not None
    assert guide_history == []


def test_search_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user)

    guides = []
    for _ in range(5):
        guides.append(create_random_guide(db, faker, user, signature, False))

    random_guide = random.choice(guides)

    r = client.get(
        f"{settings.API_V1_STR}/guide/?id={random_guide.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    guide_search = r.json()
    assert guide_search is not None
    assert guide_search["result"] == []

    random_guide = random.choice(guides)

    r = client.get(
        f"{settings.API_V1_STR}/guide/?id={random_guide.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    guide_search = r.json()
    assert guide_search is not None
    assert guide_search["totalCount"] == 1
    assert any(i["id"] == random_guide.id for i in guide_search["result"])

    random_guide = random.choice(guides)

    r = client.get(
        f"{settings.API_V1_STR}/guide/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    guide_search = r.json()
    assert guide_search is not None
    assert guide_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/guide/?id=!{random_guide.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_guide.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/guide/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/guide/?id=({guides[0].id},{guides[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == guides[0].id
    assert r.json()["result"][3]["id"] == guides[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/guide/?id=!({guides[0].id},{guides[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != guides[0].id for a in r.json()["result"])
    assert any(a["id"] != guides[1].id for a in r.json()["result"])
    assert any(a["id"] != guides[2].id for a in r.json()["result"])
    assert any(a["id"] != guides[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/guide/?id=[{guides[0].id},{guides[4].id},{guides[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == guides[0].id
    assert r.json()["result"][1]["id"] == guides[2].id
    assert r.json()["result"][2]["id"] == guides[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/guide/?id=![{guides[0].id},{guides[4].id},{guides[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != guides[0].id for a in r.json()["result"])
    assert all(a["id"] != guides[2].id for a in r.json()["result"])
    assert all(a["id"] != guides[4].id for a in r.json()["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/guide/?tlp={random_guide.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] == random_guide.id for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/guide/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/guide/?status={random_guide.status.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] == random_guide.id for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/guide/?status={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/guide/?entry_count={random_guide.entry_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] == random_guide.id for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/guide/?entry_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/guide/?subject={random_guide.subject[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] == random_guide.id for a in r.json()["result"])


def test_get_signatures_guide(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user)
    guide = create_random_guide(db, faker, user, signature, False)

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}/signatures",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/guide/-1/signatures",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/guide/{guide.id}/signatures",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    guide_signatures = r.json()
    assert guide_signatures is not None
    assert any(i["id"] == signature.id for i in guide_signatures)
