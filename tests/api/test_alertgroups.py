import random

from urllib.parse import quote_plus
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum, StatusEnum
from app.core.config import settings

from tests.utils.alert import create_random_alert
from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.user import create_random_user
from tests.utils.entity import create_random_entity
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source


def test_get_alertgroup(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user.username)

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    alertgroup_data = r.json()
    assert alertgroup_data is not None
    assert alertgroup_data["id"] == alertgroup.id


def test_create_alertgroup(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alerts = []
    for _ in range(2):
        alerts.append(create_random_alert(db, faker, user.username))

    data = {
        "owner": user.username,
        "alerts": [],
    }

    r = client.post(
        f"{settings.API_V1_STR}/alertgroup",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    alertgroup_data = r.json()
    assert alertgroup_data is not None
    assert alertgroup_data["id"] > 0
    assert alertgroup_data["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/alertgroup",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    alertgroup_data = r.json()
    assert alertgroup_data is not None
    assert alertgroup_data["id"] > 0
    assert alertgroup_data["owner"] == data["owner"]


def test_update_alertgroup(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, owner.username)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/alertgroup/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    alertgroup_data = r.json()
    assert alertgroup_data is not None
    assert alertgroup_data["id"] == alertgroup.id
    assert alertgroup_data["subject"] == data["subject"]
    assert alertgroup_data["subject"] != alertgroup.subject


def test_delete_alertgroup(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user.username)

    r = client.delete(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    alertgroup_data = r.json()
    assert alertgroup_data is not None
    assert alertgroup_data["id"] == alertgroup.id

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/alertgroup/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_undelete_alertgroup(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user.username)

    r = client.delete(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/alertgroup/undelete?target_id=-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/alertgroup/undelete?target_id={alertgroup.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/alertgroup/undelete?target_id={alertgroup.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    alertgroup_data = r.json()
    assert alertgroup_data is not None
    assert alertgroup_data["id"] == alertgroup.id


def test_entities_alertgroup(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user.username)
    entity = create_random_entity(db, faker, TargetTypeEnum.alertgroup, alertgroup.id)

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/entity",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/-1/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_history_alertgroup(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user.username)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    alertgroup_data = r.json()
    assert any(i["audit_data"]["subject"] == data["subject"] for i in alertgroup_data)
    assert alertgroup_data[0]["audit_data"]["subject"] == data["subject"]

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403


def test_reflair_alertgroup(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user.username)

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/reflair",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/-1/reflair",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/reflair",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    alertgroup_flair = r.json()
    assert alertgroup_flair is not None
    assert alertgroup_flair["id"] == alertgroup.id


def test_search_alertgroups(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroups = []
    for _ in range(5):
        alertgroups.append(create_random_alertgroup_no_sig(db, faker, user.username))

    random_alertgroup = random.choice(alertgroups)

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup?id={random_alertgroup.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    search_result = r.json()
    assert search_result["totalCount"] == 0
    assert search_result["resultCount"] == 0

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?id={random_alertgroup.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alertgroup = r.json()
    assert api_alertgroup["totalCount"] == 1
    assert api_alertgroup["resultCount"] == 1
    assert api_alertgroup["result"][0]["id"] == random_alertgroup.id

    # int negations
    random_alertgroup = random.choice(alertgroups)
    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?id=!{random_alertgroup.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["id"] != random_alertgroup.id for a in api_alert["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?id=({alertgroups[0].id},{alertgroups[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert api_alert["result"][0]["id"] == alertgroups[0].id
    assert api_alert["result"][3]["id"] == alertgroups[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?id=!({alertgroups[0].id},{alertgroups[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert any(a["id"] != alertgroups[0].id for a in api_alert["result"])
    assert any(a["id"] != alertgroups[1].id for a in api_alert["result"])
    assert any(a["id"] != alertgroups[2].id for a in api_alert["result"])
    assert any(a["id"] != alertgroups[3].id for a in api_alert["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?id=[{alertgroups[0].id},{alertgroups[4].id},{alertgroups[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert len(api_alert["result"]) == 3
    assert api_alert["result"][0]["id"] == alertgroups[0].id
    assert api_alert["result"][1]["id"] == alertgroups[2].id
    assert api_alert["result"][2]["id"] == alertgroups[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?id=![{alertgroups[0].id},{alertgroups[4].id},{alertgroups[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["id"] != alertgroups[0].id for a in api_alert["result"])
    assert all(a["id"] != alertgroups[2].id for a in api_alert["result"])
    assert all(a["id"] != alertgroups[4].id for a in api_alert["result"])

    random_alertgroup = random.choice(alertgroups)

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?subject={random_alertgroup.subject}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_alertgroup.id

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?subject=!{random_alertgroup.subject}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["id"] != random_alertgroup.id for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?status={StatusEnum.open.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["open_count"] > 0 for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?status=!{StatusEnum.open.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["open_count"] == 0 for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?status={StatusEnum.closed.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["closed_count"] > 0 for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?status=!{StatusEnum.closed.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["closed_count"] == 0 for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?status={StatusEnum.promoted.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["promoted_count"] > 0 for a in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?status=!{StatusEnum.promoted.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert all(a["promoted_count"] == 0 for a in r.json()["result"])

    random_alertgroup = random.choice(alertgroups)
    tag = create_random_tag(db, faker, TargetTypeEnum.alertgroup, random_alertgroup.id)

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_alertgroup.id

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert len(r.json()["result"]) == 0

    random_alertgroup = random.choice(alertgroups)
    source = create_random_source(db, faker, TargetTypeEnum.alertgroup, random_alertgroup.id)

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_alertgroup.id

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert len(r.json()["result"]) == 0

    # type checking
    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?tlp={random_alertgroup.tlp.name}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert any(i["id"] == random_alertgroup.id for i in api_alert["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?alert_count={random_alertgroup.alert_count}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert any(i["id"] == random_alertgroup.id for i in api_alert["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?alert_count={faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?first_view={quote_plus(random_alertgroup.first_view.isoformat())}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_alert = r.json()
    assert any(i["id"] == random_alertgroup.id for i in api_alert["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?first_view={faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422

    true_alertgroup = create_random_alertgroup_no_sig(db, faker, parsed=True)
    for b in ['y', 'yes', 't', 'true', 'on', '1', True]:
        r = client.get(
            f"{settings.API_V1_STR}/alertgroup/?parsed={b}",
            headers=superuser_token_headers
        )

        assert r.status_code == 200
        api_alert = r.json()
        assert any(i["id"] == true_alertgroup.id for i in api_alert["result"])

    false_alertgroup = create_random_alertgroup_no_sig(db, faker, parsed=False)
    for b in ['n', 'no', 'f', 'false', 'off', '0', False]:
        r = client.get(
            f"{settings.API_V1_STR}/alertgroup/?parsed={b}",
            headers=superuser_token_headers
        )

        assert r.status_code == 200
        api_alert = r.json()
        assert any(i["id"] == false_alertgroup.id for i in api_alert["result"])

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/?parsed={faker.word()}_{faker.word()}",
        headers=superuser_token_headers
    )

    assert r.status_code == 422


def test_read_alert_group_alerts(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user.username)

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/alerts",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/-1/alerts",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/alerts",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    alerts_data = r.json()
    assert alerts_data is not None
    assert any(i["id"] == alertgroup.alerts[0].id for i in alerts_data)


def test_add_alertgroup_alert(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, user.username)

    data = {
        "owner": user.username,
    }

    r = client.post(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/alerts",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/alertgroup/9999999999/alerts",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/alertgroup/{alertgroup.id}/alerts",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    alert_data = r.json()
    assert alert_data is not None
    assert alert_data["id"] > 0
    assert alert_data["alertgroup_id"] == alertgroup.id
