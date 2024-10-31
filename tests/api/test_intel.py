import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import StatusEnum, TlpEnum, TargetTypeEnum, EntryClassEnum

from tests.utils.user import create_random_user
from tests.utils.intel import create_random_intel
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entry import create_random_entry
from tests.utils.entity import create_random_entity
from tests.utils.promotion import promote_intel_to_product


def test_get_intel(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username)

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/intel/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    intel_data = r.json()
    assert intel_data is not None
    assert intel_data["id"] == intel.id


def test_create_intel(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    data = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "status": random.choice(list(StatusEnum)).value,
        "subject": faker.sentence()
    }

    r = client.post(
        f"{settings.API_V1_STR}/intel",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    intel_data = r.json()
    assert intel_data is not None
    assert intel_data["id"] > 0
    assert intel_data["subject"] == data["subject"]

    r = client.post(
        f"{settings.API_V1_STR}/intel",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422


def test_update_intel(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/intel/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    intel_data = r.json()
    assert intel_data is not None
    assert intel_data["id"] == intel.id
    assert intel_data["subject"] != intel.subject
    assert intel_data["subject"] == data["subject"]


def test_delete_intel(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username, False)

    r = client.delete(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/intel/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    intel_data = r.json()
    assert intel_data is not None
    assert intel_data["id"] == intel.id

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_undelete_intel(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username, False)

    r = client.delete(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/intel/undelete?target_id={intel.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/intel/undelete?target_id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/intel/undelete?target_id={intel.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    intel_data = r.json()
    assert intel_data is not None
    assert intel_data["id"] == intel.id


def test_entries_intel(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username, False)
    entry = create_random_entry(db, faker, owner.username, target_type=TargetTypeEnum.intel, target_id=intel.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id

    r = client.get(
        f"{settings.API_V1_STR}/intel/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0
    assert len(entry_data["result"]) == 0


def test_tag_untag_intel(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username, False)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/intel/{intel.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_intel = r.json()
    assert any([i for i in tag_intel["tags"] if i["id"] == tag.id])

    r = client.post(
        f"{settings.API_V1_STR}/intel/-1/tag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/intel/{intel.id}/tag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/intel/-1/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/intel/{intel.id}/untag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/intel/{intel.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_intel = r.json()
    assert tag_intel["tags"] == []


def test_source_add_remove_intel(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username, False)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/intel/{intel.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_intel = r.json()
    assert any([i for i in source_intel["sources"] if i["id"] == source.id])

    r = client.post(
        f"{settings.API_V1_STR}/intel/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/intel/{intel.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/intel/{intel.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_intel = r.json()
    assert source_intel["sources"] == []

    r = client.post(
        f"{settings.API_V1_STR}/intel/-1/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/intel/{intel.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422


def test_entities_intel(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username, False)
    entity = create_random_entity(db, faker, TargetTypeEnum.intel, intel.id)

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}/entity",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id

    r = client.get(
        f"{settings.API_V1_STR}/intel/-1/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0


def test_history_intel(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = create_random_intel(db, faker, owner.username, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/intel/{intel.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    intel_data = r.json()
    assert any(i["audit_data"]["subject"] == data["subject"] for i in intel_data)
    assert intel_data[0]["audit_data"]["subject"] == data["subject"]

    r = client.get(
        f"{settings.API_V1_STR}/intel/{intel.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/intel/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    intel_data = r.json()
    assert intel_data == []


def test_search_intel(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    intels = []
    for _ in range(5):
        intels.append(create_random_intel(db, faker, owner.username, False))

    random_intel = random.choice(intels)

    r = client.get(
        f"{settings.API_V1_STR}/intel/?id={random_intel.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    intel_search = r.json()
    assert intel_search is not None
    assert intel_search["result"] == []

    random_intel = random.choice(intels)

    r = client.get(
        f"{settings.API_V1_STR}/intel/?id={random_intel.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    intel_search = r.json()
    assert intel_search is not None
    assert intel_search["totalCount"] == 1
    assert any(i["id"] == random_intel.id for i in intel_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/intel/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    intel_search = r.json()
    assert intel_search is not None
    assert intel_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/intel/?id=!{random_intel.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_intel.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/intel/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/intel/?id=({intels[0].id},{intels[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == intels[0].id
    assert r.json()["result"][3]["id"] == intels[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/intel/?id=!({intels[0].id},{intels[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != intels[0].id for a in r.json()["result"])
    assert any(a["id"] != intels[1].id for a in r.json()["result"])
    assert any(a["id"] != intels[2].id for a in r.json()["result"])
    assert any(a["id"] != intels[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/intel/?id=[{intels[0].id},{intels[4].id},{intels[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == intels[0].id
    assert r.json()["result"][1]["id"] == intels[2].id
    assert r.json()["result"][2]["id"] == intels[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/intel/?id=![{intels[0].id},{intels[4].id},{intels[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != intels[0].id for a in r.json()["result"])
    assert all(a["id"] != intels[2].id for a in r.json()["result"])
    assert all(a["id"] != intels[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.intel, random_intel.id)

    r = client.get(
        f"{settings.API_V1_STR}/intel/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_intel.id

    r = client.get(
        f"{settings.API_V1_STR}/intel/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_intel.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.intel, random_intel.id)

    r = client.get(
        f"{settings.API_V1_STR}/intel/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_intel.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/intel/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_intel.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/intel/?tlp={random_intel.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_intel.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/intel/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/intel/?subject={random_intel.subject[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_intel.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/intel/?entry_count={random_intel.entry_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_intel.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/intel/?entry_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    intel = create_random_intel(db, faker)
    product = promote_intel_to_product(db, [intel.id])

    r = client.get(
        f"{settings.API_V1_STR}/intel/?promoted_to=product:{product.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == intel.id

    intel1 = create_random_intel(db, faker)
    promote_intel_to_product(db, [intel1.id])

    r = client.get(
        f"{settings.API_V1_STR}/intel/?promoted_to=!product:{product.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert any(i["id"] == intel1.id for i in api_dispatch["result"])
    assert all(i["id"] != intel.id for i in api_dispatch["result"])
