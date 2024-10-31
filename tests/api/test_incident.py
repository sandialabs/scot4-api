import random

from datetime import datetime
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import StatusEnum, TlpEnum, TargetTypeEnum, EntryClassEnum

from tests.utils.user import create_random_user
from tests.utils.incident import create_random_incident
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity
from tests.utils.entry import create_random_entry
from tests.utils.promotion import promote_event_to_incident
from tests.utils.event import create_random_event


def test_get_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username)

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/incident/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    incident_data = r.json()
    assert incident_data is not None
    assert incident_data["id"] == incident.id


def test_create_incident(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    occurred_date = faker.past_datetime()
    discovered_date = faker.date_time_between_dates(occurred_date, datetime.now())

    data = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "occurred_date": occurred_date.isoformat(),
        "discovered_date": discovered_date.isoformat(),
        "reported_date": faker.date_time_between_dates(discovered_date, datetime.now()).isoformat(),
        "status": random.choice(list(StatusEnum)).value,
        "subject": faker.sentence(),
        "data_ver": str(faker.pyfloat(1, 1, True)),
        "entry_count": faker.pyint(1, 50),
        "view_count": faker.pyint(1, 100)
    }

    r = client.post(
        f"{settings.API_V1_STR}/incident",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    incident_data = r.json()
    assert incident_data is not None
    assert incident_data["id"] > 0
    assert incident_data["subject"] == data["subject"]

    r = client.post(
        f"{settings.API_V1_STR}/incident",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/incident/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    incident_data = r.json()
    assert incident_data is not None
    assert incident_data["id"] == incident.id
    assert incident_data["subject"] != incident.subject
    assert incident_data["subject"] == data["subject"]


def test_delete_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username, False)

    r = client.delete(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=normal_user_token_headers,
    )

    assert 400 <= r.status_code < 500

    r = client.delete(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    incident_data = r.json()
    assert incident_data is not None
    assert incident_data["id"] == incident.id

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=superuser_token_headers,
    )

    assert 400 <= r.status_code < 500


def test_undelete_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username, False)

    r = client.delete(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/incident/undelete?target_id={incident.id}",
        headers=normal_user_token_headers,
    )

    assert 400 <= r.status_code < 500

    r = client.post(
        f"{settings.API_V1_STR}/incident/undelete?target_id={incident.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    incident_data = r.json()
    assert incident_data is not None
    assert incident_data["id"] == incident.id


def test_entries_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username, False)
    entry = create_random_entry(db, faker, owner.username, target_type=TargetTypeEnum.incident, target_id=incident.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}/entry",
        headers=normal_user_token_headers
    )
    assert 400 <= r.status_code < 500

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}/entry",
        headers=superuser_token_headers
    )
    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id


def test_tag_untag_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username, False)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/incident/{incident.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )
    assert r.status_code == 200
    tag_incident = r.json()
    assert any([i for i in tag_incident["tags"] if i["id"] == tag.id])

    tag2 = create_random_tag(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/incident/{incident.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag2.id}
    )
    assert r.status_code == 200
    tag_incident = r.json()
    assert any([i for i in tag_incident["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/incident/{incident.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )
    assert r.status_code == 200
    tag_incident = r.json()
    assert any([i for i in tag_incident["tags"] if i["id"] != tag.id])


def test_source_add_remove_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username, False)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/incident/{incident.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )
    assert r.status_code == 200
    source_incident = r.json()
    assert any([i for i in source_incident["sources"] if i["id"] == source.id])

    source2 = create_random_source(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/incident/{incident.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source2.id}
    )
    assert r.status_code == 200
    source_incident = r.json()
    assert any([i for i in source_incident["sources"] if i["id"] == source2.id])

    r = client.post(
        f"{settings.API_V1_STR}/incident/{incident.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source.id}
    )
    assert r.status_code == 200
    source_incident = r.json()
    assert any([i for i in source_incident["sources"] if i["id"] != source.id])


def test_entities_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username, False)
    entity = create_random_entity(db, faker, TargetTypeEnum.incident, incident.id)

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}/entity",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/incident/-1/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}/entity",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_history_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incident = create_random_incident(db, faker, owner.username, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/incident/{incident.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    incident_data = r.json()
    assert any(i["audit_data"]["subject"] == data["subject"] for i in incident_data)
    assert incident_data[0]["audit_data"]["subject"] == data["subject"]

    r = client.get(
        f"{settings.API_V1_STR}/incident/{incident.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/incident/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    incident_data = r.json()
    assert incident_data == []


def test_search_incident(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)

    incidents = []
    for _ in range(5):
        incidents.append(create_random_incident(db, faker, owner.username, False))

    random_incident = random.choice(incidents)

    r = client.get(
        f"{settings.API_V1_STR}/incident/?id={random_incident.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    incident_search = r.json()
    assert incident_search is not None
    assert incident_search["result"] == []

    random_incident = random.choice(incidents)

    r = client.get(
        f"{settings.API_V1_STR}/incident/?id={random_incident.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    incident_search = r.json()
    assert incident_search is not None
    assert incident_search["totalCount"] == 1
    assert any(i["id"] == random_incident.id for i in incident_search["result"])

    random_incident = random.choice(incidents)

    r = client.get(
        f"{settings.API_V1_STR}/incident/?id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    incident_search = r.json()
    assert incident_search is not None
    assert incident_search["result"] == []

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/incident/?id=!{random_incident.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_incident.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/incident/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/incident/?id=({incidents[0].id},{incidents[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == incidents[0].id
    assert r.json()["result"][3]["id"] == incidents[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/incident/?id=!({incidents[0].id},{incidents[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != incidents[0].id for a in r.json()["result"])
    assert any(a["id"] != incidents[1].id for a in r.json()["result"])
    assert any(a["id"] != incidents[2].id for a in r.json()["result"])
    assert any(a["id"] != incidents[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/incident/?id=[{incidents[0].id},{incidents[4].id},{incidents[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == incidents[0].id
    assert r.json()["result"][1]["id"] == incidents[2].id
    assert r.json()["result"][2]["id"] == incidents[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/incident/?id=![{incidents[0].id},{incidents[4].id},{incidents[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != incidents[0].id for a in r.json()["result"])
    assert all(a["id"] != incidents[2].id for a in r.json()["result"])
    assert all(a["id"] != incidents[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.incident, random_incident.id)

    r = client.get(
        f"{settings.API_V1_STR}/incident/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_incident.id

    r = client.get(
        f"{settings.API_V1_STR}/incident/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_incident.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.incident, random_incident.id)

    r = client.get(
        f"{settings.API_V1_STR}/incident/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_incident.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_incident.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?tlp={random_incident.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_incident.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/incident/?subject={random_incident.subject[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_incident.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?view_count={random_incident.view_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_incident.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?view_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/incident/?status={random_incident.status.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_incident.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?status={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/incident/?entry_count={random_incident.entry_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_incident.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?entry_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    event = create_random_event(db, faker)
    incident = promote_event_to_incident(db, [event.id])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?promoted_from=event:{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == incident.id

    event1 = create_random_event(db, faker)
    incident1 = promote_event_to_incident(db, [event1.id])

    r = client.get(
        f"{settings.API_V1_STR}/incident/?promoted_from=!event:{event.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert any(i["id"] == incident1.id for i in api_dispatch["result"])
    assert all(i["id"] != incident.id for i in api_dispatch["result"])
