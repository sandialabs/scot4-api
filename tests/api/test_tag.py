import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.core.config import settings

from tests.utils.alert import create_random_alert
from tests.utils.event import create_random_event
from tests.utils.tag import create_random_tag


def test_get_tag(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/tag/0",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/tag/{tag.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["id"] == tag.id


def test_create_tag(client: TestClient, normal_user_token_headers: dict, faker: Faker) -> None:
    data = {
        "name": f"{faker.unique.word()}_{faker.pyint()}".lower(),
        "description": faker.sentence(),
    }

    r = client.post(
        f"{settings.API_V1_STR}/tag",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/tag",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["id"] >= 1
    assert tag_data["name"] == data["name"].lower()
    assert tag_data["description"] == data["description"]


def test_create_tags(client: TestClient, normal_user_token_headers: dict, faker: Faker) -> None:
    data = [{
        "name": f"{faker.unique.word()}_{faker.pyint()}".lower(),
        "description": faker.sentence(),
    },{
        "name": f"{faker.unique.word()}_{faker.pyint()}".lower(),
        "description": faker.sentence(),
    }]

    r = client.post(
        f"{settings.API_V1_STR}/tag/many",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/tag/many",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert len(tag_data) == 2
    assert tag_data[0]["id"] >= 1
    assert tag_data[0]["name"] == data[0]["name"].lower()
    assert tag_data[0]["description"] == data[0]["description"]
    assert tag_data[1]["id"] >= 1
    assert tag_data[1]["name"] == data[1]["name"].lower()
    assert tag_data[1]["description"] == data[1]["description"]
    assert tag_data[0]["id"] < tag_data[1]["id"]


def test_update_tag(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)

    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/tag/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/tag/{tag.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/tag/{tag.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["id"] == tag.id
    assert tag_data["description"] == data["description"]
    assert tag_data["description"] != tag.description


def test_update_tag(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    tag1 = create_random_tag(db, faker)
    tag2 = create_random_tag(db, faker)

    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/tag/many/?ids=-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/tag/many/?ids={tag1.id}&ids={tag2.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/tag/many/?ids={tag1.id}&ids={tag2.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert len(tag_data) == 2
    assert tag_data[0]["id"] == tag1.id
    assert tag_data[0]["description"] == data["description"]
    assert tag_data[1]["id"] == tag2.id
    assert tag_data[1]["description"] == data["description"]


def test_delete_tag(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/tag/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/tag/{tag.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["id"] == tag.id

    r = client.get(
        f"{settings.API_V1_STR}/tag/{tag.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_delete_tags(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    tag1 = create_random_tag(db, faker)
    tag2 = create_random_tag(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/tag/many/?ids=-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/tag/many/?ids={tag1.id}&ids={tag2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert len(tag_data) == 2
    assert tag_data[0]["id"] == tag1.id
    assert tag_data[1]["id"] == tag2.id

    r = client.get(
        f"{settings.API_V1_STR}/tag/{tag1.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/tag/{tag2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_undelete_tag(client: TestClient, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/tag/{tag.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/tag/undelete?target_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/tag/undelete?target_id={tag.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["id"] == tag.id


def test_search_tag(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    tags = []
    for _ in range(5):
        tags.append(create_random_tag(db, faker))

    random_tag = random.choice(tags)

    r = client.get(
        f"{settings.API_V1_STR}/tag/?id={random_tag.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    tag_search = r.json()
    assert tag_search is not None
    assert tag_search["totalCount"] == 1
    assert any(i["id"] == random_tag.id for i in tag_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/tag/?id=-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    tag_search = r.json()
    assert tag_search is not None
    assert tag_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/tag/?id=!{random_tag.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_tag.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/tag/?id={faker.word()}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/tag/?id=({tags[0].id},{tags[3].id})",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == tags[0].id
    assert r.json()["result"][3]["id"] == tags[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/tag/?id=!({tags[0].id},{tags[3].id})",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != tags[0].id for a in r.json()["result"])
    assert any(a["id"] != tags[1].id for a in r.json()["result"])
    assert any(a["id"] != tags[2].id for a in r.json()["result"])
    assert any(a["id"] != tags[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/tag/?id=[{tags[0].id},{tags[4].id},{tags[2].id}]",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == tags[0].id
    assert r.json()["result"][1]["id"] == tags[2].id
    assert r.json()["result"][2]["id"] == tags[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/tag/?id=![{tags[0].id},{tags[4].id},{tags[2].id}]",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != tags[0].id for a in r.json()["result"])
    assert all(a["id"] != tags[2].id for a in r.json()["result"])
    assert all(a["id"] != tags[4].id for a in r.json()["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/tag/?description={random_tag.description[1:-1]}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_tag.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/tag/?name={random_tag.name[1:-1]}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_tag.id for i in r.json()["result"])


def test_apply_tag(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)
    alert = create_random_alert(db, faker)

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag.id}/tag",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/tag/-1/tag",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag.id}/tag",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag.id}/tag",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["id"] == tag.id


def test_add_tag(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id,
        "tag_name": faker.word().lower(),
        "tag_description": faker.sentence()
    }

    r = client.post(
        f"{settings.API_V1_STR}/tag/tag_by_name",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/tag/tag_by_name",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/tag/tag_by_name",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["id"] >= 0
    assert tag_data["name"] == data["tag_name"].lower()


def test_remove_tag(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    tag = create_random_tag(db, faker, TargetTypeEnum.alert, alert.id)

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": alert.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag.id}/untag",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/tag/-1/untag",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag.id}/untag",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag.id}/untag",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["id"] == tag.id

    data = {
        "target_type": TargetTypeEnum.alert.value,
        "target_id": -1
    }

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag.id}/untag",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_tag_appearances(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    tag = create_random_tag(db, faker, TargetTypeEnum.alert, alert.id)

    r = client.get(
        f"{settings.API_V1_STR}/tag/{tag.id}/appearance",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["totalCount"] == 0
    assert tag_data["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/tag/-1/appearance",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["totalCount"] == 0
    assert tag_data["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/tag/{tag.id}/appearance",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    tag_data = r.json()
    assert tag_data is not None
    assert tag_data["totalCount"] == 0
    assert tag_data["resultCount"] == 0


def test_tag_replace(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    event = create_random_event(db, faker)
    tag1 = create_random_tag(db, faker, TargetTypeEnum.event, event.id)
    tag2 = create_random_tag(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert len(r.json()["tags"]) != 0
    assert any(a["id"] == tag1.id for a in r.json()["tags"])

    r = client.post(
        f"{settings.API_V1_STR}/tag/-1/replace/{tag2.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag1.id}/replace/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag1.id}/replace/{tag2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag1.id}/replace/{tag2.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == tag2.id

    r = client.get(
        f"{settings.API_V1_STR}/tag/{tag1.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/tag/{tag2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    assert r.json()["id"] == tag2.id

    r = client.get(
        f"{settings.API_V1_STR}/event/{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert len(r.json()["tags"]) != 0
    assert any(a["id"] == tag2.id for a in r.json()["tags"])


def test_tag_target_appearance(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    tag1 = create_random_tag(db, faker)
    tag2 = create_random_tag(db, faker)
    tag3 = create_random_tag(db, faker)
    
    event1 = create_random_event(db, faker, create_extras=False)
    event2 = create_random_event(db, faker, create_extras=False)
    event3 = create_random_event(db, faker, create_extras=False)
    
    # apply 2 tags to 2 events
    for tag in [tag1, tag2]:
        for event in [event1, event2]:
            r = client.post(
                f"{settings.API_V1_STR}/tag/{tag.id}/tag",
                headers=superuser_token_headers,
                json={
                    "target_type": TargetTypeEnum.event.value,
                    "target_id": event.id
                }
            )
            
            assert r.status_code == 200

    # apply 1 tag to 1 event
    r = client.post(
        f"{settings.API_V1_STR}/tag/{tag3.id}/tag",
        headers=superuser_token_headers,
        json={
            "target_type": TargetTypeEnum.event.value,
            "target_id": event3.id
        }
    )
    
    assert r.status_code == 200

    # search for 1 tag get 1 event back
    r = client.get(
        f"{settings.API_V1_STR}/tag/target_appearance/?id={tag3.id}",
        headers=normal_user_token_headers
    )
    
    assert r.status_code == 200
    assert r.json()["result"][0]["target_id"] == event3.id
    assert r.json()["result"][0]["target_type"] == TargetTypeEnum.event.value
    assert len(r.json()["result"][0]["items"]) == 1
    assert r.json()["result"][0]["items"][0]["id"] == tag3.id

    # search for 2 tags ORed get 3 events back
    r = client.get(
        f"{settings.API_V1_STR}/tag/target_appearance/?id=[{tag1.id},{tag3.id}]",
        headers=normal_user_token_headers
    )
    
    assert r.status_code == 200
    assert all([a["target_id"] in [event1.id, event2.id, event3.id] for a in r.json()["result"]])
    assert all([a["target_type"] == TargetTypeEnum.event.value for a in r.json()["result"]])
    for targets in r.json()["result"]:
        assert any([a["id"] in [tag1.id, tag3.id] for a in targets["items"]])

    # search for 2 tags ANDed get 2 events back
    r = client.get(
        settings.API_V1_STR + "/tag/target_appearance/?name={" + tag1.name + "," + tag2.name + "}",
        headers=normal_user_token_headers
    )
    
    assert r.status_code == 200
    assert all([a["target_id"] in [event1.id, event2.id, event3.id] for a in r.json()["result"]])
    assert all([a["target_type"] == TargetTypeEnum.event.value for a in r.json()["result"]])
    for targets in r.json()["result"]:
        assert any([a["id"] in [tag1.id, tag2.id] for a in targets["items"]])

    r = client.get(
        settings.API_V1_STR + "/tag/target_appearance/?id={" + str(tag1.id) + "," + str(tag2.id) + "}",
        headers=normal_user_token_headers
    )
    
    assert r.status_code == 200
    assert all([a["target_id"] in [event1.id, event2.id, event3.id] for a in r.json()["result"]])
    assert all([a["target_type"] == TargetTypeEnum.event.value for a in r.json()["result"]])
    for targets in r.json()["result"]:
        assert any([a["id"] in [tag1.id, tag2.id] for a in targets["items"]])

    # test both id a names
    r = client.get(
        f"{settings.API_V1_STR}/tag/target_appearance/?id={tag1.id}&name={tag2.name}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422

    # test with unknown tag ids
    r = client.get(
        f"{settings.API_V1_STR}/tag/target_appearance/?id=-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404
