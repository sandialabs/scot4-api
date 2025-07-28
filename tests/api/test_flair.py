import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from hashlib import md5

from app.enums import TargetTypeEnum, RemoteFlairSourceEnum
from app.core.config import settings

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.alert import create_random_alert
from tests.utils.entry import create_random_entry
from tests.utils.user import create_random_user
from tests.utils.entity import create_random_entity
from tests.utils.flair import create_remote_flair_html, create_random_remote_flair


def test_flair_update(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": alert.id,
                "type": TargetTypeEnum.alert.value
            }
        }
    )

    assert r.status_code == 422

    alertgroup = create_random_alertgroup_no_sig(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": alertgroup.id,
                "type": TargetTypeEnum.alertgroup.value
            }
        }
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": alertgroup.id,
                "type": TargetTypeEnum.alertgroup.value
            },
            "alerts": [{
                "id": alertgroup.as_dict()["alerts"][0]["id"]
            }]
        }
    )

    assert r.status_code == 200
    flair_data = r.json()
    assert flair_data is not None
    assert flair_data["id"] == alertgroup.id

    owner = create_random_user(db, faker)
    entry = create_random_entry(db, faker, owner)
    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": entry.id,
                "type": TargetTypeEnum.entry.value
            }
        }
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": -1,
                "type": TargetTypeEnum.checklist.value
            },
            "text_flaired": faker.sentence(),
            "entities": faker.pydict(value_types=[str, int, bool, float])
        }
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": -1,
                "type": TargetTypeEnum.entry.value
            },
            "text_flaired": faker.sentence(),
            "entities": faker.pydict(value_types=[str, int, bool, float])
        }
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": entry.id,
                "type": TargetTypeEnum.entry.value
            },
            "text_flaired": faker.sentence(),
            "entities": {
                faker.word(): faker.sentence(),
                "subject": faker.word()
            },
            "text_plain": faker.sentence()
        }
    )

    assert r.status_code == 200
    flair_data = r.json()
    assert flair_data is not None
    assert flair_data["id"] == entry.id

    remote_flair = create_random_remote_flair(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": remote_flair.id,
                "type": TargetTypeEnum.remote_flair.value
            },
            "entities": {
                "ipv4": {
                    faker.ipv4(): faker.pyint()  
                },
                "url": {
                    faker.url(): faker.pyint()  
                },
                "username": {
                    faker.user_name(): faker.pyint()  
                }
            }
        }
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == remote_flair.id

    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": remote_flair.id,
                "type": TargetTypeEnum.remote_flair.value
            }
        }
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/flair/flairupdate",
        headers=normal_user_token_headers,
        json={
            "target": {
                "id": -1,
                "type": TargetTypeEnum.remote_flair.value
            },
            "entities": {
                "ipv4": {
                    faker.ipv4(): faker.pyint()  
                },
                "url": {
                    faker.url(): faker.pyint()  
                },
                "username": {
                    faker.user_name(): faker.pyint()  
                }
            }
        }
    )

    assert r.status_code == 404


def test_enrich_entity(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    data = {
        "classes": faker.pylist(value_types=[str]),
        "enriched_data": faker.pydict(value_types=(str, bool, int, float))
    }
    r = client.post(
        f"{settings.API_V1_STR}/flair/enrich/-1",
        headers=normal_user_token_headers,
        json=data
    )
    assert r.status_code == 404

    entity = create_random_entity(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/flair/enrich/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/flair/enrich/{entity.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    enrich_data = r.json()
    assert enrich_data is not None
    assert enrich_data["id"] == entity.id


def test_post_remote_flair(client: TestClient, normal_user_token_headers: dict, faker: Faker) -> None:
    data = {
        "uri": faker.uri(),
        "data": create_remote_flair_html(faker),
        "source": random.choice(list(RemoteFlairSourceEnum)).value
    }

    r = client.post(
        f"{settings.API_V1_STR}/flair/remote",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["md5"] == md5(data["data"].encode("utf-8")).hexdigest()

    r = client.post(
        f"{settings.API_V1_STR}/flair/remote",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["md5"] == md5(data["data"].encode("utf-8")).hexdigest()


def test_get_remote_flair(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    remote_flair = create_random_remote_flair(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/flair/remote/{remote_flair.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == remote_flair.id

    r = client.get(
        f"{settings.API_V1_STR}/flair/remote/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404
