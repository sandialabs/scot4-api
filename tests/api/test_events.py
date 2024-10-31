import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TlpEnum, StatusEnum, TargetTypeEnum, EntryClassEnum

from tests.utils.event import create_random_event
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity
from tests.utils.entry import create_random_entry
from tests.utils.file import create_random_file
from tests.utils.promotion import promote_event_to_incident


def test_get_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username)

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    event_data = r.json()
    assert event_data["id"] == event.id

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/event/-1",
        headers=superuser_token_headers
    )
    assert r.status_code == 404


def test_create_event(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    data = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "status": random.choice(list(StatusEnum)).value,
        "subject": faker.sentence(),
        "view_count": faker.pyint()
    }

    r = client.post(
        f"{settings.API_V1_STR}/event/",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_event = r.json()
    assert created_event["id"] >= 0
    assert created_event["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/event/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/event/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    event_data = r.json()
    assert event_data["id"] == event.id
    assert event_data["subject"] == data["subject"]
    assert event_data["subject"] != event.subject


def test_delete_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username, False)

    r = client.delete(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    event_data = r.json()
    assert event_data["id"] == event.id

    r = client.delete(
        f"{settings.API_V1_STR}/event/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username, False)

    r = client.delete(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/event/undelete?target_id={event.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/event/undelete?target_id={event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    delete_event = r.json()
    assert delete_event is not None
    assert delete_event["id"] == event.id

    r = client.post(
        f"{settings.API_V1_STR}/event/undelete?target_id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_entries_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username, False)
    entry = create_random_entry(db, faker, owner.username, target_type=TargetTypeEnum.event, target_id=event.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/event/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0
    assert len(entry_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id


def test_tag_untag_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username, False)
    tag1 = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag1.id}
    )

    assert r.status_code == 200
    tag_event = r.json()
    assert tag_event is not None
    assert any([i for i in tag_event["tags"] if i["id"] == tag1.id])

    tag2 = create_random_tag(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag2.id}
    )

    assert r.status_code == 200
    tag_event = r.json()
    assert tag_event is not None
    assert any([i for i in tag_event["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/event/-1/tag",
        headers=superuser_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/tag",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 200
    tag_event = r.json()
    assert tag_event is not None
    assert any([i for i in tag_event["tags"] if i["id"] != tag1.id])

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 200
    tag_event = r.json()
    assert tag_event is not None
    assert len([i for i in tag_event["tags"] if i["id"] != tag2.id]) == 0

    r = client.post(
        f"{settings.API_V1_STR}/event/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/untag",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 422


def test_source_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username, False)
    source1 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source1.id}
    )

    assert r.status_code == 200
    source_event = r.json()
    assert source_event is not None
    assert source1.id in [i["id"] for i in source_event["sources"]]

    source2 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source2.id}
    )

    assert r.status_code == 200
    source_event = r.json()
    assert source_event is not None
    assert source2.id in [i["id"] for i in source_event["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/event/-1/add-source",
        headers=superuser_token_headers,
        json={"id": source1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/add-source",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source1.id},
    )

    assert r.status_code == 200
    source_event = r.json()
    assert source_event is not None
    assert source1.id not in [i["id"] for i in source_event["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source2.id},
    )

    assert r.status_code == 200
    source_event = r.json()
    assert source_event is not None
    assert source2.id not in [i["id"] for i in source_event["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/event/-1/remove-source",
        headers=superuser_token_headers,
        json={"id": source2.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/event/{event.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 422


def test_entities_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username, False)
    entity = create_random_entity(db, faker, TargetTypeEnum.event, event.id)

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}/entity",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/event/-1/entity",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}/entity",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_files_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username)
    file = create_random_file(db, faker, owner.username, TargetTypeEnum.event, event.id)

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}/files",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data is not None
    assert file_data["totalCount"] >= 0
    assert file_data["resultCount"] >= 0
    assert any([i for i in file_data["result"] if i["id"] == file.id])

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}/files",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/event/-1/files",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data is not None
    assert file_data["totalCount"] == 0
    assert file_data["resultCount"] == 0
    assert len(file_data["result"]) == 0


def test_history_event(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    event = create_random_event(db, faker, owner.username, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    event_data = r.json()
    assert any(i["audit_data"]["subject"] == data["subject"] for i in event_data)
    assert event_data[0]["audit_data"]["subject"] == data["subject"]

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/event/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    event_data = r.json()
    assert event_data == []


def test_search_event(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)

    events = []
    for _ in range(5):
        events.append(create_random_event(db, faker, owner.username, False))
    random_event = random.choice(events)

    r = client.get(
        f"{settings.API_V1_STR}/event/?id={random_event.id}",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    search = r.json()
    assert search["totalCount"] == 1
    assert search["resultCount"] == 1
    assert search["result"][0]["id"] == random_event.id

    # 404 if role doesn't exist
    r = client.get(
        f"{settings.API_V1_STR}/event/?id=-1",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    search = r.json()
    assert search["totalCount"] == 0
    assert search["resultCount"] == 0
    assert len(search["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/event?id={random_event.id}",
        headers=normal_user_token_headers,
    )

    search_result = r.json()
    assert 200 <= r.status_code < 300
    assert search_result["totalCount"] == 0
    assert search_result["resultCount"] == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/event/?id=!{random_event.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_event.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/event/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/event/?id=({events[0].id},{events[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == events[0].id
    assert r.json()["result"][3]["id"] == events[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/event/?id=!({events[0].id},{events[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != events[0].id for a in r.json()["result"])
    assert any(a["id"] != events[1].id for a in r.json()["result"])
    assert any(a["id"] != events[2].id for a in r.json()["result"])
    assert any(a["id"] != events[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/event/?id=[{events[0].id},{events[4].id},{events[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == events[0].id
    assert r.json()["result"][1]["id"] == events[2].id
    assert r.json()["result"][2]["id"] == events[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/event/?id=![{events[0].id},{events[4].id},{events[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != events[0].id for a in r.json()["result"])
    assert all(a["id"] != events[2].id for a in r.json()["result"])
    assert all(a["id"] != events[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.event, random_event.id)

    r = client.get(
        f"{settings.API_V1_STR}/event/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_event.id

    r = client.get(
        f"{settings.API_V1_STR}/event/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_event.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.event, random_event.id)

    r = client.get(
        f"{settings.API_V1_STR}/event/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_event.id

    r = client.get(
        f"{settings.API_V1_STR}/event/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_event.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/event/?subject={random_event.subject[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_event.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/event/?view_count={random_event.view_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_event.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/event/?view_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/event/?status={random_event.status.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_event.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/event/?status={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/event/?entry_count={random_event.entry_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_event.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/event/?entry_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    random_event = random.choice(events)
    incident = promote_event_to_incident(db, [random_event.id])

    r = client.get(
        f"{settings.API_V1_STR}/event/?promoted_to=incident:{incident.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == random_event.id

    random_event1 = random.choice(events)
    promote_event_to_incident(db, [random_event1.id])

    r = client.get(
        f"{settings.API_V1_STR}/event/?promoted_to=!incident:{incident.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == random_event1.id
