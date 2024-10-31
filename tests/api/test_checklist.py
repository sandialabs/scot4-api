import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TlpEnum, TargetTypeEnum
from tests.utils.checklist import create_random_checklist
from tests.utils.tag import create_random_tag


def test_get_checklist(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    checklist = create_random_checklist(db, faker)
    r = client.get(
        f"{settings.API_V1_STR}/checklist/{checklist.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    get_checklist = r.json()
    assert get_checklist is not None
    assert get_checklist["id"] == checklist.id

    r = client.get(
        f"{settings.API_V1_STR}/checklist/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/checklist/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_create_checklist(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker) -> None:
    data = {
        "owner": faker.word(),
        "tlp": random.choice(list(TlpEnum)).value,
        "subject": faker.sentence(12),
        "checklist_data_ver": str(faker.pyfloat(1, 1, True)),
        "checklist_data": faker.pydict(value_types=[int, str, float]),
    }

    r = client.post(
        f"{settings.API_V1_STR}/checklist/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200
    create_checklist = r.json()
    assert create_checklist is not None
    assert create_checklist["id"] is not None
    assert create_checklist["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/checklist/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    create_checklist = r.json()
    assert create_checklist is not None
    assert create_checklist["id"] is not None
    assert create_checklist["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/checklist/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_checklist(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    checklist = create_random_checklist(db, faker)
    data = {
        "tlp": TlpEnum.white.value,
        "checklist_data_ver": str(faker.pyfloat(1, 1, True)),
    }

    r = client.put(
        f"{settings.API_V1_STR}/checklist/{checklist.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    get_checklist = r.json()
    assert get_checklist is not None
    assert get_checklist["tlp"] != checklist.tlp
    assert get_checklist["tlp"] == data["tlp"]

    r = client.put(
        f"{settings.API_V1_STR}/checklist/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/checklist/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/checklist/{checklist.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422


def test_delete_checklist(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    checklist = create_random_checklist(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/checklist/{checklist.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/checklist/{checklist.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    delete_checklist = r.json()
    assert delete_checklist is not None
    assert delete_checklist["id"] == checklist.id

    r = client.get(
        f"{settings.API_V1_STR}/checklist/{checklist.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/checklist/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_undelete_checklist(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    checklist = create_random_checklist(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/checklist/{checklist.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/checklist/undelete?target_id={checklist.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/checklist/undelete?target_id={checklist.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    delete_checklist = r.json()
    assert delete_checklist is not None
    assert delete_checklist["id"] == checklist.id

    r = client.post(
        f"{settings.API_V1_STR}/checklist/undelete?target_id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_taguntag_checklist(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    checklist = create_random_checklist(db, faker)
    tag1 = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/checklist/{checklist.id}/tag",
        headers=normal_user_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/checklist/{checklist.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 200
    tag_checklist = r.json()
    assert tag_checklist is not None
    assert any([i for i in tag_checklist["tags"] if i["id"] == tag1.id])

    tag2 = create_random_tag(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/checklist/{checklist.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 200
    tag_checklist = r.json()
    assert tag_checklist is not None
    assert any([i for i in tag_checklist["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/checklist/-1/tag",
        headers=superuser_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/checklist/{checklist.id}/untag",
        headers=normal_user_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/checklist/{checklist.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 200
    tag_checklist = r.json()
    assert tag_checklist is not None
    assert any([i for i in tag_checklist["tags"] if i["id"] != tag1.id])

    r = client.post(
        f"{settings.API_V1_STR}/checklist/{checklist.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 200
    tag_checklist = r.json()
    assert tag_checklist is not None
    assert len(tag_checklist["tags"]) == 0

    r = client.post(
        f"{settings.API_V1_STR}/checklist/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 404


def test_search_checklist(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    checklists = []
    for _ in range(5):
        checklists.append(create_random_checklist(db, faker))

    random_checklist = random.choice(checklists)
    r = client.get(
        f"{settings.API_V1_STR}/checklist?id={random_checklist.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    search_result = r.json()
    assert search_result["totalCount"] == 0
    assert search_result["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/checklist?id={random_checklist.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_checklist = r.json()
    assert api_checklist["totalCount"] == 1
    assert api_checklist["resultCount"] == 1
    assert api_checklist["result"][0]["id"] == random_checklist.id

    tag = create_random_tag(db, faker, TargetTypeEnum.checklist, random_checklist.id)

    r = client.get(
        f"{settings.API_V1_STR}/checklist/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_checklist.id

    r = client.get(
        f"{settings.API_V1_STR}/checklist/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 0

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/checklist/?owner={random_checklist.owner}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_checklist.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/checklist/?subject={random_checklist.subject[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_checklist.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/checklist/?checklist_data_ver={random_checklist.checklist_data_ver}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_checklist.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/checklist/?tlp={random_checklist.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_checklist.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/checklist/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422
