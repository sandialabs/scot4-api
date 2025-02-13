import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.enums import TargetTypeEnum, PopularityMetricEnum
from tests.utils.entry import create_random_entry
from tests.utils.popularity import create_random_popularity


def test_get_popularity(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    popularity = create_random_popularity(db, faker)
    r = client.get(
        f"{settings.API_V1_STR}/popularity/{popularity.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == popularity.id

    r = client.get(
        f"{settings.API_V1_STR}/popularity/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/popularity/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_create_popularity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    user = crud.user.get_by_username(db, username=settings.EMAIL_TEST_USER)
    entry = create_random_entry(db, faker)

    data = {
        "target_type": TargetTypeEnum.entry.value,
        "target_id": entry.id,
        "metric_type": PopularityMetricEnum.upvote.value,
        "owner_id": user.id,
    }

    r = client.post(
        f"{settings.API_V1_STR}/popularity/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] is not None
    assert r.json()["owner_id"] == data["owner_id"]

    # creating the same thing does nothing
    r = client.post(
        f"{settings.API_V1_STR}/popularity/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 422

    # creating with the opposite metric type will update as long as target_id/type and owner are the same
    data["metric_type"] = PopularityMetricEnum.downvote.value
    r = client.post(
        f"{settings.API_V1_STR}/popularity/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 422


def test_update_popularity(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    popularity = create_random_popularity(db, faker, owner=user)
    data = {
        "target_type": random.choice(list(TargetTypeEnum)).value,
    }

    r = client.put(
        f"{settings.API_V1_STR}/popularity/{popularity.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 422

    data = {
        "metric_type": random.choice(list(PopularityMetricEnum)).value,
    }

    r = client.put(
        f"{settings.API_V1_STR}/popularity/{popularity.id}",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/popularity/{popularity.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["metric_type"] == data["metric_type"]

    r = client.put(
        f"{settings.API_V1_STR}/popularity/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/popularity/{popularity.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422


def test_delete_popularity(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    popularity = create_random_popularity(db, faker, owner=user)

    r = client.delete(
        f"{settings.API_V1_STR}/popularity/{popularity.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/popularity/{popularity.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json() is not None
    assert r.json()["id"] == popularity.id

    r = client.get(
        f"{settings.API_V1_STR}/popularity/{popularity.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/popularity/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_upvote_downvote(client: TestClient, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    entry = create_random_entry(db, faker, user)

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/upvote", headers=superuser_token_headers
    )

    assert r.status_code == 200

    assert r.json() is not None
    assert r.json()["id"] == entry.id
    assert r.json()["popularity_voted"] == PopularityMetricEnum.upvote.value

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/upvote", headers=superuser_token_headers
    )

    assert r.status_code == 200

    assert r.json() is not None
    assert r.json()["id"] == entry.id
    assert r.json()["popularity_voted"] is None

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/downvote", headers=superuser_token_headers
    )

    assert r.status_code == 200

    assert r.json() is not None
    assert r.json()["id"] == entry.id
    assert r.json()["popularity_voted"] == PopularityMetricEnum.downvote.value

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/downvote", headers=superuser_token_headers
    )

    assert r.status_code == 200

    assert r.json() is not None
    assert r.json()["id"] == entry.id
    assert r.json()["popularity_voted"] is None

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/upvote", headers=superuser_token_headers
    )

    assert r.status_code == 200

    assert r.json() is not None
    assert r.json()["id"] == entry.id
    assert r.json()["popularity_voted"] == PopularityMetricEnum.upvote.value

    r = client.post(
        f"{settings.API_V1_STR}/entry/{entry.id}/downvote", headers=superuser_token_headers
    )

    assert r.status_code == 200

    assert r.json() is not None
    assert r.json()["id"] == entry.id
    assert r.json()["popularity_voted"] == PopularityMetricEnum.downvote.value
