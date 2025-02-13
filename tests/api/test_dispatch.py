import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TlpEnum, TargetTypeEnum
from tests.utils.dispatch import create_random_dispatch
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity
from tests.utils.promotion import promote_dispatch_to_intel


def test_get_dispatch(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, user)
    r = client.get(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    get_dispatch = r.json()
    assert get_dispatch is not None
    assert get_dispatch["id"] == dispatch.id

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_create_dispatch(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker) -> None:
    data = {
        "owner": faker.word(),
        "tlp": random.choice(list(TlpEnum)).value,
        "subject": faker.sentence(12),
        "dispatch_data_ver": str(faker.pyfloat(1, 1, True)),
        "dispatch_data": faker.pydict(value_types=[int, str, float]),
    }

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200
    create_dispatch = r.json()
    assert create_dispatch is not None
    assert create_dispatch["id"] is not None
    assert create_dispatch["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    create_dispatch = r.json()
    assert create_dispatch is not None
    assert create_dispatch["id"] is not None
    assert create_dispatch["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_dispatch(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, user, False)
    data = {
        "tlp": TlpEnum.white.value,
        "dispatch_data_ver": str(faker.pyfloat(1, 1, True)),
    }

    r = client.put(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    get_dispatch = r.json()
    assert get_dispatch is not None
    assert get_dispatch["tlp"] != dispatch.tlp
    assert get_dispatch["tlp"] == data["tlp"]

    r = client.put(
        f"{settings.API_V1_STR}/dispatch/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/dispatch/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422


def test_delete_dispatch(client: TestClient, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, user, False)

    r = client.delete(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    delete_dispatch = r.json()
    assert delete_dispatch is not None
    assert delete_dispatch["id"] == dispatch.id

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/dispatch/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_undelete_dispatch(client: TestClient, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, user, False)

    r = client.delete(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    delete_dispatch = r.json()
    assert delete_dispatch is not None
    assert delete_dispatch["id"] == dispatch.id

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/undelete?target_id={dispatch.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    delete_dispatch = r.json()
    assert delete_dispatch is not None
    assert delete_dispatch["id"] == dispatch.id

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/undelete?target_id={dispatch.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422


def test_tag_untag_dispatch(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, user, False)
    tag1 = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/tag",
        headers=normal_user_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 200
    tag_dispatch = r.json()
    assert tag_dispatch is not None
    assert any([i for i in tag_dispatch["tags"] if i["id"] == tag1.id])

    tag2 = create_random_tag(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 200
    tag_dispatch = r.json()
    assert tag_dispatch is not None
    assert any([i for i in tag_dispatch["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/-1/tag",
        headers=superuser_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/untag",
        headers=normal_user_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 200
    tag_dispatch = r.json()
    assert tag_dispatch is not None
    assert any([i for i in tag_dispatch["tags"] if i["id"] != tag1.id])

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 200
    tag_dispatch = r.json()
    assert tag_dispatch is not None
    assert len([i for i in tag_dispatch["tags"] if i["id"] != tag2.id]) == 0

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 404


def test_source_add_remove_dispatch(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, owner, False)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/add-source",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert 200 <= r.status_code < 300
    source_dispatch = r.json()
    assert any([i for i in source_dispatch["sources"] if i["id"] == source.id])

    source2 = create_random_source(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source2.id}
    )

    assert 200 <= r.status_code < 300
    source_dispatch = r.json()
    assert any([i for i in source_dispatch["sources"] if i["id"] == source2.id])

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )

    assert 200 <= r.status_code < 300
    source_dispatch = r.json()
    assert any([i for i in source_dispatch["sources"] if i["id"] != source.id])


def test_entities_dispatch(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, owner, False)
    entity = create_random_entity(db, faker, TargetTypeEnum.dispatch, dispatch.id)

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/entity",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/-1/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/entity",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_history_dispatch(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, owner, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    dispatch_data = r.json()
    assert any(i["audit_data"]["subject"] == data["subject"] for i in dispatch_data)
    assert dispatch_data[0]["audit_data"]["subject"] == data["subject"]

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/{dispatch.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    dispatch_data = r.json()
    assert len(dispatch_data) == 0


def test_search_dispatch(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    despatches = []
    for _ in range(5):
        despatches.append(create_random_dispatch(db, faker, owner, False))

    random_dispatch = random.choice(despatches)

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id={random_dispatch.id}",
        headers=normal_user_token_headers
    )

    assert 200 <= r.status_code < 300
    dispatch_search = r.json()
    assert dispatch_search is not None
    assert dispatch_search["result"] == []

    random_dispatch = random.choice(despatches)

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id={random_dispatch.id}",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    dispatch_search = r.json()
    assert dispatch_search is not None
    assert dispatch_search["totalCount"] == 1
    assert any(i["id"] == random_dispatch.id for i in dispatch_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id=-1",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    dispatch_search = r.json()
    assert dispatch_search is not None
    assert dispatch_search["result"] == []

    # int negations
    random_dispatch = random.choice(despatches)
    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id=!{random_dispatch.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert all(a["id"] != random_dispatch.id for a in api_dispatch["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id=({despatches[0].id},{despatches[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert api_dispatch["result"][0]["id"] == despatches[0].id
    assert api_dispatch["result"][3]["id"] == despatches[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id=!({despatches[0].id},{despatches[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert any(a["id"] != despatches[0].id for a in api_dispatch["result"])
    assert any(a["id"] != despatches[1].id for a in api_dispatch["result"])
    assert any(a["id"] != despatches[2].id for a in api_dispatch["result"])
    assert any(a["id"] != despatches[3].id for a in api_dispatch["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id=[{despatches[0].id},{despatches[4].id},{despatches[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 3
    assert api_dispatch["result"][0]["id"] == despatches[0].id
    assert api_dispatch["result"][1]["id"] == despatches[2].id
    assert api_dispatch["result"][2]["id"] == despatches[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?id=![{despatches[0].id},{despatches[4].id},{despatches[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert all(a["id"] != despatches[0].id for a in api_dispatch["result"])
    assert all(a["id"] != despatches[2].id for a in api_dispatch["result"])
    assert all(a["id"] != despatches[4].id for a in api_dispatch["result"])

    random_dispatch = random.choice(despatches)
    intel = promote_dispatch_to_intel(db, [random_dispatch.id])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?promoted_to=intel:{intel.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == random_dispatch.id

    random_dispatch1 = random.choice(despatches)
    promote_dispatch_to_intel(db, [random_dispatch1.id])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?promoted_to=!intel:{intel.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == random_dispatch1.id

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?owner={random_dispatch.owner}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == random_dispatch.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?tlp={random_dispatch.tlp.name}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == random_dispatch.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?status={random_dispatch.status.name}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == random_dispatch.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?status={faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    tag = create_random_tag(db, faker, TargetTypeEnum.dispatch, random_dispatch.id)

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_dispatch.id

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_dispatch.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.dispatch, random_dispatch.id)

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_dispatch.id

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_dispatch.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?subject={random_dispatch.subject[1:-1]}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    assert any(i["id"] == random_dispatch.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?entry_count={random_dispatch.entry_count}",
        headers=superuser_token_headers
    )

    print(r.json())
    assert r.status_code == 200
    assert any(i["id"] == random_dispatch.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/dispatch/?entry_count={faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422
