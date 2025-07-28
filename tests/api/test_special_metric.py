import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import timezone, datetime

from app.core.config import settings
from app.enums import TargetTypeEnum, SpecialMetricEnum

from tests.utils.special_metric import create_random_special_metric


def test_get_special_metric(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    special_metric = create_random_special_metric(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    special_metric_data = r.json()
    assert special_metric_data["id"] == special_metric.id

    r = client.get(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=normal_user_token_headers
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/special_metric/0",
        headers=superuser_token_headers
    )
    assert r.status_code == 404


def test_create_special_metric(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    _start_time = faker.date_time_this_month(tzinfo=timezone.utc)

    data = {
        "target_id": faker.pyint(),
        "target_type": random.choice(list(TargetTypeEnum)).value,
        "metric_type": random.choice(list(SpecialMetricEnum)).value,
        "start_time": _start_time.isoformat(),
        "end_time": faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc).isoformat()
    }

    r = client.post(
        f"{settings.API_V1_STR}/special_metric/",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_special_metric = r.json()
    assert created_special_metric["id"] >= 0
    assert created_special_metric["target_id"] == data["target_id"]

    r = client.post(
        f"{settings.API_V1_STR}/special_metric/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403


def test_create_special_metrics(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    _start_time = faker.date_time_this_month(tzinfo=timezone.utc)

    data = [{
        "target_id": faker.pyint(),
        "target_type": random.choice(list(TargetTypeEnum)).value,
        "metric_type": random.choice(list(SpecialMetricEnum)).value,
        "start_time": _start_time.isoformat(),
        "end_time": faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc).isoformat()
    },{
        "target_id": faker.pyint(),
        "target_type": random.choice(list(TargetTypeEnum)).value,
        "metric_type": random.choice(list(SpecialMetricEnum)).value,
        "start_time": _start_time.isoformat(),
        "end_time": faker.date_time_between(start_date=_start_time, tzinfo=timezone.utc).isoformat()
    }]

    r = client.post(
        f"{settings.API_V1_STR}/special_metric/many/",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_special_metric = r.json()
    assert len(created_special_metric) == 2
    assert created_special_metric[0]["id"] >= 0
    assert created_special_metric[0]["target_id"] == data[0]["target_id"]
    assert created_special_metric[1]["id"] >= 0
    assert created_special_metric[1]["target_id"] == data[1]["target_id"]
    assert created_special_metric[0]["id"] < created_special_metric[1]["id"]

    r = client.post(
        f"{settings.API_V1_STR}/special_metric/many/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403


def test_update_special_metric(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    special_metric = create_random_special_metric(db, faker)

    data = {
        "end_time": datetime.now(timezone.utc).isoformat()
    }

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    special_metric_data = r.json()
    assert special_metric_data["id"] == special_metric.id
    assert datetime.fromisoformat(special_metric_data["end_time"]) == datetime.fromisoformat(data["end_time"])
    assert datetime.fromisoformat(special_metric_data["end_time"]) != special_metric.end_time


def test_update_special_metrics(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    special_metric1 = create_random_special_metric(db, faker)
    special_metric2 = create_random_special_metric(db, faker)

    data = {
        "end_time": datetime.now(timezone.utc).isoformat()
    }

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/many/?ids={special_metric1.id}&ids={special_metric2.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/many/?ids=-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/many/?ids={special_metric1.id}&ids={special_metric2.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/many/?ids={special_metric1.id}&ids={special_metric2.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    special_metric_data = r.json()
    assert len(special_metric_data) == 2
    assert special_metric_data[0]["id"] == special_metric1.id
    assert datetime.fromisoformat(special_metric_data[0]["end_time"]) == datetime.fromisoformat(data["end_time"])
    assert datetime.fromisoformat(special_metric_data[0]["end_time"]) != special_metric1.end_time
    assert special_metric_data[1]["id"] == special_metric2.id
    assert datetime.fromisoformat(special_metric_data[0]["end_time"]) == datetime.fromisoformat(data["end_time"])
    assert datetime.fromisoformat(special_metric_data[0]["end_time"]) != special_metric2.end_time


def test_delete_special_metric(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    special_metric = create_random_special_metric(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    special_metric_data = r.json()
    assert special_metric_data["id"] == special_metric.id

    r = client.delete(
        f"{settings.API_V1_STR}/special_metric/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_delete_special_metrics(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    special_metric1 = create_random_special_metric(db, faker)
    special_metric2 = create_random_special_metric(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/special_metric/many/?ids={special_metric1.id}&ids={special_metric2.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/special_metric/many/?ids={special_metric1.id}&ids={special_metric2.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    special_metric_data = r.json()
    assert len(special_metric_data) == 2
    assert special_metric_data[0]["id"] == special_metric1.id
    assert special_metric_data[1]["id"] == special_metric2.id

    r = client.delete(
        f"{settings.API_V1_STR}/special_metric/many/?ids=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_special_metric(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    special_metric = create_random_special_metric(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/special_metric/undelete?target_id={special_metric.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/special_metric/undelete?target_id={special_metric.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    delete_special_metric = r.json()
    assert delete_special_metric is not None
    assert delete_special_metric["id"] == special_metric.id

    r = client.post(
        f"{settings.API_V1_STR}/special_metric/undelete?target_id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_history_special_metric(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    special_metric = create_random_special_metric(db, faker)

    data = {
        "end_time": datetime.now(timezone.utc).isoformat()
    }

    r = client.put(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    special_metric_data = r.json()
    assert any(datetime.fromisoformat(i["audit_data"]["end_time"]) == datetime.fromisoformat(data["end_time"]) for i in special_metric_data)

    r = client.get(
        f"{settings.API_V1_STR}/special_metric/{special_metric.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/special_metric/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    special_metric_data = r.json()
    assert special_metric_data == []


def test_search_special_metric(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    special_metrics = []
    for _ in range(5):
        special_metrics.append(create_random_special_metric(db, faker))
    random_special_metric = random.choice(special_metrics)
    print(random_special_metric.id)

    r = client.get(
        f"{settings.API_V1_STR}/special_metric/?id={random_special_metric.id}",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    search = r.json()
    print(settings.API_V1_STR)
    print(search)
    assert search["totalCount"] == 1
    assert search["resultCount"] == 1
    assert search["result"][0]["id"] == random_special_metric.id

    # 404 if role doesn't exist
    r = client.get(
        f"{settings.API_V1_STR}/special_metric/?id=-1",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    search = r.json()
    assert search["totalCount"] == 0
    assert search["resultCount"] == 0
    assert len(search["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/special_metric?id={random_special_metric.id}",
        headers=normal_user_token_headers,
    )

    search_result = r.json()
    assert 200 <= r.status_code < 300
    assert search_result["totalCount"] == 1
    assert search_result["resultCount"] == 1

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/special_metric/?id=!{random_special_metric.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_special_metric.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/special_metric/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/special_metric/?id=({special_metrics[0].id},{special_metrics[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == special_metrics[0].id
    assert r.json()["result"][3]["id"] == special_metrics[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/special_metric/?id=!({special_metrics[0].id},{special_metrics[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != special_metrics[0].id for a in r.json()["result"])
    assert any(a["id"] != special_metrics[1].id for a in r.json()["result"])
    assert any(a["id"] != special_metrics[2].id for a in r.json()["result"])
    assert any(a["id"] != special_metrics[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/special_metric/?id=[{special_metrics[0].id},{special_metrics[4].id},{special_metrics[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == special_metrics[0].id
    assert r.json()["result"][1]["id"] == special_metrics[2].id
    assert r.json()["result"][2]["id"] == special_metrics[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/special_metric/?id=![{special_metrics[0].id},{special_metrics[4].id},{special_metrics[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != special_metrics[0].id for a in r.json()["result"])
    assert all(a["id"] != special_metrics[2].id for a in r.json()["result"])
    assert all(a["id"] != special_metrics[4].id for a in r.json()["result"])
