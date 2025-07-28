import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TlpEnum, StatusEnum, TargetTypeEnum, EntryClassEnum

from tests.utils.vuln_feed import create_random_vuln_feed
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity
from tests.utils.entry import create_random_entry
from tests.utils.file import create_random_file


def test_get_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_feed_data = r.json()
    assert vuln_feed_data["id"] == vuln_feed.id

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/0",
        headers=superuser_token_headers
    )
    assert r.status_code == 404


def test_create_vuln_feed(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    data = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "status": random.choice(list(StatusEnum)).value,
        "subject": faker.sentence(),
        "view_count": faker.pyint()
    }

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_vuln_feed = r.json()
    assert created_vuln_feed["id"] >= 0
    assert created_vuln_feed["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_create_vuln_feeds(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    data = [{
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "status": random.choice(list(StatusEnum)).value,
        "subject": faker.sentence(),
        "view_count": faker.pyint()
    },{
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "status": random.choice(list(StatusEnum)).value,
        "subject": faker.sentence(),
        "view_count": faker.pyint()
    }]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/many/",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_vuln_feed = r.json()
    assert len(created_vuln_feed) == 2
    assert created_vuln_feed[0]["id"] >= 0
    assert created_vuln_feed[0]["owner"] == data[0]["owner"]
    assert created_vuln_feed[1]["id"] >= 0
    assert created_vuln_feed[1]["owner"] == data[1]["owner"]
    assert created_vuln_feed[0]["id"] < created_vuln_feed[1]["id"]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/many/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    vuln_feed_data = r.json()
    assert vuln_feed_data["id"] == vuln_feed.id
    assert vuln_feed_data["subject"] == data["subject"]
    assert vuln_feed_data["subject"] != vuln_feed.subject


def test_update_vuln_feeds(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed1 = create_random_vuln_feed(db, faker, owner, False)
    vuln_feed2 = create_random_vuln_feed(db, faker, owner, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/many/?ids={vuln_feed1.id}&ids={vuln_feed2.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/many/?ids=-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/many/?ids={vuln_feed1.id}&ids={vuln_feed2.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/many/?ids={vuln_feed1.id}&ids={vuln_feed2.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    vuln_feed_data = r.json()
    assert len(vuln_feed_data) == 2
    assert vuln_feed_data[0]["id"] == vuln_feed1.id
    assert vuln_feed_data[0]["subject"] == data["subject"]
    assert vuln_feed_data[1]["id"] == vuln_feed2.id
    assert vuln_feed_data[1]["subject"] == data["subject"]


def test_delete_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner, False)

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_feed_data = r.json()
    assert vuln_feed_data["id"] == vuln_feed.id

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_feed/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_delete_vuln_feeds(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed1 = create_random_vuln_feed(db, faker, owner, False)
    vuln_feed2 = create_random_vuln_feed(db, faker, owner, False)

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_feed/many/?ids={vuln_feed1.id}&ids={vuln_feed2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_feed/many/?ids={vuln_feed1.id}&ids={vuln_feed2.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_feed_data = r.json()
    assert len(vuln_feed_data) == 2
    assert vuln_feed_data[0]["id"] == vuln_feed1.id
    assert vuln_feed_data[1]["id"] == vuln_feed2.id

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_feed/many/?ids=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner, False)

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/undelete?target_id={vuln_feed.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/undelete?target_id={vuln_feed.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    delete_vuln_feed = r.json()
    assert delete_vuln_feed is not None
    assert delete_vuln_feed["id"] == vuln_feed.id

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/undelete?target_id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_entries_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner, False)
    entry = create_random_entry(db, faker, owner, target_type=TargetTypeEnum.vuln_feed, target_id=vuln_feed.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0
    assert len(entry_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id


def test_tag_untag_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner, False)
    tag1 = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag1.id}
    )

    assert r.status_code == 200
    tag_vuln_feed = r.json()
    assert tag_vuln_feed is not None
    assert any([i for i in tag_vuln_feed["tags"] if i["id"] == tag1.id])

    tag2 = create_random_tag(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag2.id}
    )

    assert r.status_code == 200
    tag_vuln_feed = r.json()
    assert tag_vuln_feed is not None
    assert any([i for i in tag_vuln_feed["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/-1/tag",
        headers=superuser_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/tag",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 200
    tag_vuln_feed = r.json()
    assert tag_vuln_feed is not None
    assert any([i for i in tag_vuln_feed["tags"] if i["id"] != tag1.id])

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 200
    tag_vuln_feed = r.json()
    assert tag_vuln_feed is not None
    assert len([i for i in tag_vuln_feed["tags"] if i["id"] != tag2.id]) == 0

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/untag",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 422


def test_source_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner, False)
    source1 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source1.id}
    )

    assert r.status_code == 200
    source_vuln_feed = r.json()
    assert source_vuln_feed is not None
    assert source1.id in [i["id"] for i in source_vuln_feed["sources"]]

    source2 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source2.id}
    )

    assert r.status_code == 200
    source_vuln_feed = r.json()
    assert source_vuln_feed is not None
    assert source2.id in [i["id"] for i in source_vuln_feed["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/-1/add-source",
        headers=superuser_token_headers,
        json={"id": source1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/add-source",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source1.id},
    )

    assert r.status_code == 200
    source_vuln_feed = r.json()
    assert source_vuln_feed is not None
    assert source1.id not in [i["id"] for i in source_vuln_feed["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source2.id},
    )

    assert r.status_code == 200
    source_vuln_feed = r.json()
    assert source_vuln_feed is not None
    assert source2.id not in [i["id"] for i in source_vuln_feed["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/-1/remove-source",
        headers=superuser_token_headers,
        json={"id": source2.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 422


def test_entities_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner, False)
    entity = create_random_entity(db, faker, TargetTypeEnum.vuln_feed, vuln_feed.id)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/entity",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/-1/entity",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/entity",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_files_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner)
    file = create_random_file(db, faker, owner, TargetTypeEnum.vuln_feed, vuln_feed.id)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/files",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data is not None
    assert file_data["totalCount"] >= 0
    assert file_data["resultCount"] >= 0
    assert any([i for i in file_data["result"] if i["id"] == file.id])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/files",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/-1/files",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data is not None
    assert file_data["totalCount"] == 0
    assert file_data["resultCount"] == 0
    assert len(file_data["result"]) == 0


def test_history_vuln_feed(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, owner, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_feed_data = r.json()
    assert any(i["audit_data"]["subject"] == data["subject"] for i in vuln_feed_data)
    assert vuln_feed_data[0]["audit_data"]["subject"] == data["subject"]

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/{vuln_feed.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_feed_data = r.json()
    assert vuln_feed_data == []


def test_search_vuln_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)

    vuln_feeds = []
    for _ in range(5):
        vuln_feeds.append(create_random_vuln_feed(db, faker, owner, False))
    random_vuln_feed = random.choice(vuln_feeds)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?id={random_vuln_feed.id}",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    search = r.json()
    assert search["totalCount"] == 1
    assert search["resultCount"] == 1
    assert search["result"][0]["id"] == random_vuln_feed.id

    # 404 if role doesn't exist
    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?id=-1",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    search = r.json()
    assert search["totalCount"] == 0
    assert search["resultCount"] == 0
    assert len(search["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed?id={random_vuln_feed.id}",
        headers=normal_user_token_headers,
    )

    search_result = r.json()
    assert 200 <= r.status_code < 300
    assert search_result["totalCount"] == 0
    assert search_result["resultCount"] == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?id=!{random_vuln_feed.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_vuln_feed.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?id=({vuln_feeds[0].id},{vuln_feeds[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == vuln_feeds[0].id
    assert r.json()["result"][3]["id"] == vuln_feeds[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?id=!({vuln_feeds[0].id},{vuln_feeds[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != vuln_feeds[0].id for a in r.json()["result"])
    assert any(a["id"] != vuln_feeds[1].id for a in r.json()["result"])
    assert any(a["id"] != vuln_feeds[2].id for a in r.json()["result"])
    assert any(a["id"] != vuln_feeds[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?id=[{vuln_feeds[0].id},{vuln_feeds[4].id},{vuln_feeds[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == vuln_feeds[0].id
    assert r.json()["result"][1]["id"] == vuln_feeds[2].id
    assert r.json()["result"][2]["id"] == vuln_feeds[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?id=![{vuln_feeds[0].id},{vuln_feeds[4].id},{vuln_feeds[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != vuln_feeds[0].id for a in r.json()["result"])
    assert all(a["id"] != vuln_feeds[2].id for a in r.json()["result"])
    assert all(a["id"] != vuln_feeds[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.vuln_feed, random_vuln_feed.id)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_vuln_feed.id

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_vuln_feed.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.vuln_feed, random_vuln_feed.id)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_vuln_feed.id

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_vuln_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?subject={random_vuln_feed.subject[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_vuln_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?view_count={random_vuln_feed.view_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_vuln_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?view_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?status={random_vuln_feed.status.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_vuln_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?status={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?entry_count={random_vuln_feed.entry_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_vuln_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_feed/?entry_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422
