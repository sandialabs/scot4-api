import random

from urllib.parse import quote_plus
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum, EntryClassEnum
from app.core.config import settings

from tests.utils.user import create_random_user
from tests.utils.feed import create_random_feed
from tests.utils.entry import create_random_entry
from tests.utils.entity import create_random_entity


def test_get_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    feed = create_random_feed(db, faker, owner)

    r = client.get(
        f"{settings.API_V1_STR}/feed/{feed.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    feed_data = r.json()
    assert feed_data["id"] == feed.id

    r = client.get(
        f"{settings.API_V1_STR}/feed/{feed.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/feed/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_create_feed(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session):
    owner = create_random_user(db, faker)
    data = {
        "name": faker.word(),
        "owner": owner.username,
        "type": faker.word(),
        "uri": faker.url()
    }

    r = client.post(
        f"{settings.API_V1_STR}/feed/",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_feed = r.json()
    assert created_feed["id"] >= 0
    assert created_feed["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/feed/",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422


def test_update_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    feed = create_random_feed(db, faker, owner)
    data = {
        "status": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/feed/{feed.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    feed_data = r.json()
    assert feed_data["id"] == feed.id
    assert feed_data["status"] == data["status"]
    assert feed_data["status"] != feed.status

    owner = create_random_user(db, faker)
    feed = create_random_feed(db, faker, owner)
    data = {
        "status": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/feed/{feed.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/feed/{feed.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/feed/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_delete_feed(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    feed = create_random_feed(db, faker, owner)

    r = client.delete(
        f"{settings.API_V1_STR}/feed/{feed.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/feed/{feed.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.delete(
        f"{settings.API_V1_STR}/feed/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_feed_history(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    feed = create_random_feed(db, faker, owner)

    data = {
        "status": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/feed/{feed.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/feed/{feed.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    feed_data = r.json()
    assert feed_data is not None
    assert any(i["audit_data"]["status"] == data["status"] for i in feed_data)

    r = client.get(
        f"{settings.API_V1_STR}/feed/{feed.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/feed/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    feed_data = r.json()
    assert feed_data is not None
    assert feed_data == []


def test_feed_entries(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    feed = create_random_feed(db, faker, owner)
    entry = create_random_entry(db, faker, owner, target_type=TargetTypeEnum.feed, target_id=feed.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/feed/{feed.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/feed/{feed.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id

    r = client.get(
        f"{settings.API_V1_STR}/feed/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0
    assert len(entry_data["result"]) == 0


def test_feed_entities(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    feed = create_random_feed(db, faker, owner)
    entity = create_random_entity(db, faker, TargetTypeEnum.feed, feed.id)

    r = client.get(
        f"{settings.API_V1_STR}/feed/{feed.id}/entity",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/feed/{feed.id}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id

    r = client.get(
        f"{settings.API_V1_STR}/feed/-1/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0


def test_search_feeds(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    feeds = []
    for _ in range(5):
        feeds.append(create_random_feed(db, faker, owner))
    random_feed = random.choice(feeds)

    r = client.get(
        f"{settings.API_V1_STR}/feed/?id={random_feed.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    search = r.json()
    assert search["totalCount"] == 1
    assert search["resultCount"] == 1
    assert search["result"][0]["id"] == random_feed.id

    r = client.get(
        f"{settings.API_V1_STR}/feed/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    search = r.json()
    assert search["totalCount"] == 0
    assert search["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/feed/?id={random_feed.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    search = r.json()
    assert search["totalCount"] == 0
    assert search["resultCount"] == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/feed/?id=!{random_feed.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_feed.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/feed/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/feed/?id=({feeds[0].id},{feeds[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == feeds[0].id
    assert r.json()["result"][3]["id"] == feeds[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/feed/?id=!({feeds[0].id},{feeds[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != feeds[0].id for a in r.json()["result"])
    assert any(a["id"] != feeds[1].id for a in r.json()["result"])
    assert any(a["id"] != feeds[2].id for a in r.json()["result"])
    assert any(a["id"] != feeds[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/feed/?id=[{feeds[0].id},{feeds[4].id},{feeds[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == feeds[0].id
    assert r.json()["result"][1]["id"] == feeds[2].id
    assert r.json()["result"][2]["id"] == feeds[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/feed/?id=![{feeds[0].id},{feeds[4].id},{feeds[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != feeds[0].id for a in r.json()["result"])
    assert all(a["id"] != feeds[2].id for a in r.json()["result"])
    assert all(a["id"] != feeds[4].id for a in r.json()["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/feed/?status={random_feed.status}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/feed/?uri={random_feed.uri[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/feed/?type={random_feed.type}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/feed/?article_count={random_feed.article_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/feed/?article_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/feed/?promotions_count={random_feed.promotions_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/feed/?promotions_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/feed/?last_article={quote_plus(random_feed.last_article.isoformat())}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/feed/?last_article={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/feed/?last_attempt={quote_plus(random_feed.last_attempt.isoformat())}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_feed.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/feed/?last_attempt={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422
