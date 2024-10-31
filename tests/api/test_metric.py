from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.metric import create_random_metric
from tests.utils.audit import create_audit
from tests.utils.alert import create_random_alert


def test_get_metrics(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/metric",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    metric_data = r.json()
    assert metric_data is not None
    assert len(metric_data) == 0

    metrics = []
    for _ in range(3):
        alert = create_random_alert(db, faker)
        audit = create_audit(db, faker, alert.owner, alert)
        metrics.append(create_random_metric(db, faker, audit))

    r = client.get(
        f"{settings.API_V1_STR}/metric",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    metric_data = r.json()
    assert metric_data is not None
    assert len(metric_data) == len(metrics)
    assert any(i["id"] == metrics[0].id for i in metric_data)


def test_create_metric(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    audit = create_audit(db, faker, alert.owner, alert)

    data = {
        "name": faker.word(),
        "tooltip": faker.sentence(),
        "parameters": {
            "what": audit.what,
            "type": audit.thing_type,
            "id": audit.thing_id,
            "data": audit.audit_data
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/metric",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/metric",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/metric",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    metric_data = r.json()
    assert metric_data is not None
    assert metric_data["id"] > 0
    assert metric_data["name"] == data["name"]


def test_get_results(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    audit = create_audit(db, faker, alert.owner, alert)
    metric = create_random_metric(db, faker, audit)

    r = client.get(
        f"{settings.API_V1_STR}/metric/results",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    metric_data = r.json()
    assert metric_data is not None
    assert any(i["name"] == metric.name for i in metric_data)


def test_get_metric(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/metric/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    alert = create_random_alert(db, faker)
    audit = create_audit(db, faker, alert.owner, alert)
    metric = create_random_metric(db, faker, audit)

    r = client.get(
        f"{settings.API_V1_STR}/metric/{metric.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    metric_data = r.json()
    assert metric_data is not None
    assert metric.id == metric_data["id"]
