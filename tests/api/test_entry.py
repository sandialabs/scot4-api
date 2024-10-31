import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import TlpEnum, TargetTypeEnum, EntryClassEnum
from app.core.config import settings

from tests.utils.alert import create_random_alert
from tests.utils.user import create_random_user
from tests.utils.entry import create_random_entry, generate_html_entry
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity


def test_update_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entry = create_random_entry(db, faker, user.username)
    data_raw, data_flaired, _ = generate_html_entry(faker)

    data = {
        "entry_data": {
            "html": data_raw,
            "flaired_html": data_flaired,
            "flaired": True,
        },
    }

    r = client.put(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/entry/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["id"] == entry.id


def test_delete_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entry = create_random_entry(db, faker, user.username)

    r = client.delete(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/entry/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["id"] == entry.id

    r = client.get(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entry = create_random_entry(db, faker, user.username)

    r = client.delete(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/entry/undelete?target_id={entry.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entry/undelete?target_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entry/undelete?target_id={entry.id}",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["id"] == entry.id


def test_tag_untag_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entry = create_random_entry(db, faker, user.username)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_entry = r.json()
    assert any([i for i in tag_entry["tags"] if i["id"] == tag.id])

    tag2 = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entry/-1/tag",
        headers=normal_user_token_headers,
        json={"id": tag2.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/tag",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag2.id}
    )

    assert r.status_code == 200
    tag_entry = r.json()
    assert any([i for i in tag_entry["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/entry/-1/tag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entry/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/untag",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/untag",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )
    assert r.status_code == 200
    tag_entry = r.json()
    assert any([i for i in tag_entry["tags"] if i["id"] != tag.id])


def test_source_add_remove_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entry = create_random_entry(db, faker, owner.username)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_entry = r.json()
    assert any([i for i in source_entry["sources"] if i["id"] == source.id])

    source2 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entry/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": source2.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/add-source",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source2.id}
    )

    assert r.status_code == 200
    source_entry = r.json()
    assert any([i for i in source_entry["sources"] if i["id"] == source2.id])

    r = client.post(
        f"{settings.API_V1_STR}/entry/-1/remove-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/remove-source",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    source_entry = r.json()
    assert any([i for i in source_entry["sources"] if i["id"] != source.id])


def test_entities_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entry = create_random_entry(db, faker, owner.username)
    entity = create_random_entity(db, faker, TargetTypeEnum.entry, entry.id)

    r = client.get(
        f"{settings.API_V1_STR}/entry/{entry.id}/entity",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/entry/-1/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/entry/{entry.id}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] >= 1
    assert entity_data["totalCount"] >= 1
    assert any(i["id"] == entity.id for i in entity_data["result"])


def test_reflair_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entry = create_random_entry(db, faker, owner.username)

    r = client.get(
        f"{settings.API_V1_STR}/entry/{entry.id}/reflair",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/entry/-1/reflair",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/entry/{entry.id}/reflair",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_flair = r.json()
    assert entry_flair is not None
    assert entry_flair["id"] == entry.id


def test_get_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entry = create_random_entry(db, faker, user.username)

    r = client.get(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/entry/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/entry/{entry.id}",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["id"] == entry.id


def test_create_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user.username)
    data_raw, data_flaired, _ = generate_html_entry(faker)

    data = {
        "entry": {
            "owner": user.username,
            "tlp": random.choice(list(TlpEnum)).value,
            "target_type": TargetTypeEnum.alert.value,
            "target_id": alert.id,
            "entry_class": EntryClassEnum.entry.value,
            "entry_data": {
                "html": data_raw,
                "flaired_html": data_flaired,
                "flaired": True,
            },
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/entry",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/entry",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["id"] > 0
    assert entry_data["tlp"] == data["entry"]["tlp"]


def test_search_entry(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    entries = []
    for _ in range(5):
        entries.append(create_random_entry(db, faker, owner.username, assignee=faker.word(), status=faker.word()))

    random_entry = random.choice(entries)

    r = client.get(
        f"{settings.API_V1_STR}/entry/?id={random_entry.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entry_search = r.json()
    assert entry_search is not None
    assert entry_search["result"] == []

    random_entry = random.choice(entries)

    r = client.get(
        f"{settings.API_V1_STR}/entry/?id={random_entry.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_search = r.json()
    assert entry_search is not None
    assert entry_search["totalCount"] == 1
    assert any(i["id"] == random_entry.id for i in entry_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entry/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_search = r.json()
    assert entry_search is not None
    assert entry_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/entry/?id=!{random_entry.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_entry.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/entry/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/entry/?id=({entries[0].id},{entries[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == entries[0].id
    assert r.json()["result"][3]["id"] == entries[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/entry/?id=!({entries[0].id},{entries[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != entries[0].id for a in r.json()["result"])
    assert any(a["id"] != entries[1].id for a in r.json()["result"])
    assert any(a["id"] != entries[2].id for a in r.json()["result"])
    assert any(a["id"] != entries[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/entry/?id=[{entries[0].id},{entries[4].id},{entries[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == entries[0].id
    assert r.json()["result"][1]["id"] == entries[2].id
    assert r.json()["result"][2]["id"] == entries[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/entry/?id=![{entries[0].id},{entries[4].id},{entries[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != entries[0].id for a in r.json()["result"])
    assert all(a["id"] != entries[2].id for a in r.json()["result"])
    assert all(a["id"] != entries[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.entry, random_entry.id)

    r = client.get(
        f"{settings.API_V1_STR}/entry/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_entry.id

    r = client.get(
        f"{settings.API_V1_STR}/entry/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_entry.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.entry, random_entry.id)

    r = client.get(
        f"{settings.API_V1_STR}/entry/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_entry.id

    r = client.get(
        f"{settings.API_V1_STR}/entry/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_entry.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entry/?tlp={random_entry.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entry.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entry/?tlp={faker.word}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/entry/?target_type={random_entry.target_type.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entry.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entry/?target_type={faker.word}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/entry/?target_id={random_entry.target_id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entry.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entry/?target_id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/entry/?entry_class={random_entry.entry_class.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entry.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entry/?entry_class={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/entry/?task_assignee={random_entry.entry_data['assignee']}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200

    assert any(i["id"] == random_entry.id for i in r.json()["result"])
    r = client.get(
        f"{settings.API_V1_STR}/entry/?task_status={random_entry.entry_data['status']}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entry.id for i in r.json()["result"])
