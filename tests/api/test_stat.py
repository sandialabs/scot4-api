import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.scot_stat import create_random_stat


import pytest
pytest.skip("Stat api is currently disabled", allow_module_level=True)


def test_read_stat(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    stat = create_random_stat(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/stat/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/stat/{stat.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    stat_json = r.json()
    assert stat_json["id"] == stat.id


def test_search_stat(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    stats = []
    for _ in range(5):
        stats.append(create_random_stat(db, faker))

    random_stat = random.choice(stats)

    r = client.get(
        f"{settings.API_V1_STR}/stat/?id={random_stat.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    stat_search = r.json()
    assert stat_search["totalCount"] == 0
    assert stat_search["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/stat/?id={random_stat.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    stat_search = r.json()
    assert stat_search is not None
    assert stat_search["totalCount"] == 1
    assert any(i["id"] == random_stat.id for i in stat_search["result"])

    r = client.get(
        f"{settings.API_V1_STR}/stat/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    stat_search = r.json()
    assert stat_search is not None
    assert stat_search["result"] == []
