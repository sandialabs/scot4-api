from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.core.config import settings

from tests.utils.intel import create_random_intel
from tests.utils.user import create_random_user
from tests.utils.alert import create_random_alert
from tests.utils.event import create_random_event


def test_promote_new(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    intel = create_random_intel(db, faker, user, False)

    data = {
        "source": [{
            "type": TargetTypeEnum.intel.value,
            "id": intel.id
        }],
        "destination": TargetTypeEnum.event.value
    }

    r = client.post(
        f"{settings.API_V1_STR}/promotion",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/promotion",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/promotion",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    promote_data = r.json()
    assert promote_data["promoted_from_sources"][0]["p0_type"] == TargetTypeEnum.intel.value
    assert promote_data["promoted_from_sources"][0]["p0_id"] == intel.id
    assert promote_data["promoted_from_sources"][0]["p1_type"] == TargetTypeEnum.event.value
    assert promote_data["promoted_from_sources"][0]["p1_id"] >= 0

    r = client.get(
        f"{settings.API_V1_STR}/event/{promote_data['id']}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    intel_data = r.json()
    assert intel_data["id"] == promote_data["id"]
    assert intel_data["subject"] == promote_data["subject"]
    assert intel_data["tlp"] == promote_data["tlp"]


def test_promote_existing(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    event = create_random_event(db, faker, user, False)

    data = {
        "source": [{
            "type": TargetTypeEnum.alert.value,
            "id": alert.id
        }],
        "destination": TargetTypeEnum.event.value,
        "destination_id": event.id
    }

    r = client.post(
        f"{settings.API_V1_STR}/promotion",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/promotion",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/promotion",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    promote_data = r.json()
    assert promote_data["promoted_from_sources"][0]["p0_type"] == TargetTypeEnum.alert.value
    assert promote_data["promoted_from_sources"][0]["p0_id"] == alert.id
    assert promote_data["promoted_from_sources"][0]["p1_type"] == TargetTypeEnum.event.value
    assert promote_data["promoted_from_sources"][0]["p1_id"] == event.id

    r = client.get(
        f"{settings.API_V1_STR}/event/{promote_data['id']}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    incident_data = r.json()
    assert incident_data["id"] == promote_data["id"]
    assert incident_data["subject"] == promote_data["subject"]
    assert incident_data["tlp"] == promote_data["tlp"]
