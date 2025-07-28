import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.enums import TlpEnum, TargetTypeEnum, EntryClassEnum

from tests.utils.alert import create_random_alert
from tests.utils.user import create_random_user
from tests.utils.entry import create_random_entry
from tests.utils.entity import create_random_entity
from tests.utils.promotion import promote_alert_to_event


def test_get_alert(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert api_alert["owner"] == alert.owner
    assert api_alert["tlp"] == alert.tlp.value
    assert api_alert["status"] == alert.status.value
    assert api_alert["parsed"] == alert.parsed
    assert api_alert["data"] == alert.data

    r = client.get(
        f"{settings.API_V1_STR}/alert/0",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_create_alert(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert_data = faker.pydict(value_types=[str])

    data = {"owner": user.username, "data": alert_data}
    r = client.post(
        f"{settings.API_V1_STR}/alert/",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    created_alert = r.json()
    assert created_alert["owner"] == user.username
    assert created_alert["data"] == alert_data
    assert crud.alert.get(db, created_alert["id"]) is not None

    data = {"owner": user.username, "data": alert_data}
    r = client.post(
        f"{settings.API_V1_STR}/alert/",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200
    created_alert = r.json()
    assert created_alert["owner"] == user.username
    assert created_alert["data"] == alert_data
    assert crud.alert.get(db, created_alert["id"]) is not None


def test_create_many_alerts(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)

    data = [
        {"owner": user.username, "data": faker.pydict(value_types=[str])},
        {"owner": user.username, "data": faker.pydict(value_types=[str])},
    ]
    r = client.post(
        f"{settings.API_V1_STR}/alert/many",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    created_alert = r.json()
    assert len(created_alert) == 2
    assert created_alert[0]["owner"] == user.username
    assert created_alert[0]["data"] == data[0]["data"]
    assert created_alert[1]["owner"] == user.username
    assert created_alert[1]["data"] == data[1]["data"]
    assert crud.alert.get(db, created_alert[0]["id"]) is not None
    assert crud.alert.get(db, created_alert[1]["id"]) is not None
    assert created_alert[0]["id"] < created_alert[1]["id"]


def test_update_alert(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alert = create_random_alert(db, faker, owner)

    tlp_list = [a.value for a in list(TlpEnum)]
    tlp_list.remove(alert.tlp.value)
    data = {
        "tlp": random.choice(tlp_list)
    }

    r = client.put(
        f"{settings.API_V1_STR}/alert/{alert.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/alert/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/alert/{alert.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    alert_data = r.json()
    assert alert_data is not None
    assert alert_data["id"] == alert.id
    assert alert_data["tlp"] == data["tlp"]
    assert alert_data["tlp"] != alert.tlp


def test_update_alerts(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alert1 = create_random_alert(db, faker, owner)
    alert2 = create_random_alert(db, faker, owner)

    data = {
        "tlp": random.choice(list(TlpEnum)).value
    }

    r = client.put(
        f"{settings.API_V1_STR}/alert/many/?ids={alert1.id}&ids={alert2.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/alert/many/?ids=-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/alert/many/?ids={alert1.id}&ids={alert2.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    alert_data = r.json()
    assert alert_data is not None
    assert len(alert_data) == 2
    assert alert_data[0]["id"] == alert1.id
    assert alert_data[0]["tlp"] == data["tlp"]
    assert alert_data[1]["id"] == alert2.id
    assert alert_data[1]["tlp"] == data["tlp"]


def test_delete_alert(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)

    r = client.delete(
        f"{settings.API_V1_STR}/alert/{alert.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/alert/{alert.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    alert_data = r.json()
    assert alert_data is not None
    assert alert_data["id"] == alert.id

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/alert/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_delete_alerts(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert1 = create_random_alert(db, faker, user)
    alert2 = create_random_alert(db, faker, user)

    r = client.delete(
        f"{settings.API_V1_STR}/alert/many/?ids={alert1.id}&ids={alert2.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/alert/many/?ids={alert1.id}&ids={alert2.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    alert_data = r.json()
    assert alert_data is not None
    assert len(alert_data) == 2
    assert alert_data[0]["id"] == alert1.id
    assert alert_data[1]["id"] == alert2.id

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert1.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert2.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/alert/many/?ids=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_undelete_alert(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)

    r = client.delete(
        f"{settings.API_V1_STR}/alert/{alert.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/alert/undelete?target_id=-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/alert/undelete?target_id={alert.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/alert/undelete?target_id={alert.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    alert_data = r.json()
    assert alert_data is not None
    assert alert_data["id"] == alert.id


def test_entries_alert(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    entry = create_random_entry(db, faker, user, target_type=TargetTypeEnum.alert, target_id=alert.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/alert/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id


def test_entities_alert(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    entity = create_random_entity(db, faker, TargetTypeEnum.alert, alert.id)

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert.id}/entity",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/alert/-1/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/alert/{alert.id}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_search_alerts(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alerts = []
    for _ in range(5):
        alerts.append(create_random_alert(db, faker, owner))

    r = client.get(
        f"{settings.API_V1_STR}/alert?owner={owner.username}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    search_result = r.json()
    assert search_result["totalCount"] == 0
    assert search_result["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/alert/?owner={owner.username}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert api_alert["totalCount"] == len(alerts)
    assert api_alert["resultCount"] == len(alerts)
    assert any(x["id"] == alerts[0].id for x in api_alert["result"])

    # int negations
    random_alert = random.choice(alerts)
    r = client.get(
        f"{settings.API_V1_STR}/alert/?id=!{random_alert.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["id"] != random_alert.id for a in api_alert["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/alert/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/alert/?id=({alerts[0].id},{alerts[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert api_alert["result"][0]["id"] == alerts[0].id
    assert api_alert["result"][3]["id"] == alerts[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/alert/?id=!({alerts[0].id},{alerts[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert any(a["id"] != alerts[0].id for a in api_alert["result"])
    assert any(a["id"] != alerts[1].id for a in api_alert["result"])
    assert any(a["id"] != alerts[2].id for a in api_alert["result"])
    assert any(a["id"] != alerts[3].id for a in api_alert["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/alert/?id=[{alerts[0].id},{alerts[4].id},{alerts[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert len(api_alert["result"]) == 3
    assert api_alert["result"][0]["id"] == alerts[0].id
    assert api_alert["result"][1]["id"] == alerts[2].id
    assert api_alert["result"][2]["id"] == alerts[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/alert/?id=![{alerts[0].id},{alerts[4].id},{alerts[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["id"] != alerts[0].id for a in api_alert["result"])
    assert all(a["id"] != alerts[2].id for a in api_alert["result"])
    assert all(a["id"] != alerts[4].id for a in api_alert["result"])

    random_alert = random.choice(alerts)
    event = promote_alert_to_event(db, [random_alert.id])

    r = client.get(
        f"{settings.API_V1_STR}/alert/?promoted_to=event:{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert len(api_alert["result"]) == 1
    assert api_alert["result"][0]["id"] == random_alert.id

    random_alert1 = random.choice(alerts)
    promote_alert_to_event(db, [random_alert1.id])

    r = client.get(
        f"{settings.API_V1_STR}/alert/?promoted_to=!event:{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert any(a["id"] == random_alert1.id for a in api_alert["result"])

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/alert/?tlp={random_alert.tlp.name}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert any(i["id"] == random_alert.id for i in api_alert["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alert/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/alert/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    create_random_alert(db, faker, parsed=True)
    for b in ['y', 'yes', 't', 'true', 'on', '1', True]:
        r = client.get(
            f"{settings.API_V1_STR}/alert/?parsed={b}",
            headers=superuser_token_headers
        )

        assert r.status_code == 200
        api_alert = r.json()
        assert all(i["parsed"] == True for i in api_alert["result"])

    create_random_alert(db, faker, parsed=False)
    for b in ['n', 'no', 'f', 'false', 'off', '0', False]:
        r = client.get(
            f"{settings.API_V1_STR}/alert/?parsed={b}",
            headers=superuser_token_headers
        )

        assert r.status_code == 200
        api_alert = r.json()
        assert all(i["parsed"] == False for i in api_alert["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alert/?parsed={faker.word()}_{faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/alert/?alertgroup_id={random_alert.alertgroup_id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert any(i["id"] == random_alert.id for i in api_alert["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alert/?alertgroup_id={faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422
