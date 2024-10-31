import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.enums import EntityStatusEnum, TargetTypeEnum, EntryClassEnum, EnrichmentClassEnum

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.alert import create_random_alert
from tests.utils.entity import create_random_entity
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity_class import create_random_entity_class
from tests.utils.entity import create_random_entity_type
from tests.utils.user import create_random_user
from tests.utils.entry import create_random_entry
from tests.utils.pivot import create_random_pivot


def test_get_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker)

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data["entity_count"] == entity.entity_count
    assert entity_data["status"] == entity.status.value

    r = client.get(
        f"{settings.API_V1_STR}/entity/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404


def test_update_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker)
    data = {
        "value": faker.word()
    }

    r = client.put(
        f"{settings.API_V1_STR}/entity/{entity.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data["id"] == entity.id
    assert entity_data["value"] == data["value"]

    r = client.put(
        f"{settings.API_V1_STR}/entity/{entity.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/entity/-1",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_delete_entity(client: TestClient, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/entity/{entity.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/entity/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_entity(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker)

    r = client.delete(
        f"{settings.API_V1_STR}/entity/{entity.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/entity/undelete?target_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/undelete?target_id={entity.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["id"] == entity.id


def test_entries_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    entity = create_random_entity(db, faker)
    entry = create_random_entry(db, faker, owner.username, target_type=TargetTypeEnum.entity, target_id=entity.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id

    r = client.get(
        f"{settings.API_V1_STR}/entity/-1/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0


def test_tag_untag_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker)
    tag1 = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag1.id}
    )

    assert r.status_code == 200
    tag_entity = r.json()
    assert tag_entity is not None
    assert any([i for i in tag_entity["tags"] if i["id"] == tag1.id])

    tag2 = create_random_tag(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag2.id}
    )

    assert r.status_code == 200
    tag_entity = r.json()
    assert tag_entity is not None
    assert any([i for i in tag_entity["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/tag",
        headers=normal_user_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/tag",
        headers=normal_user_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 200
    tag_entity = r.json()
    assert tag_entity is not None
    assert any([i for i in tag_entity["tags"] if i["id"] != tag1.id])

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 200
    tag_entity = r.json()
    assert tag_entity is not None
    assert len(tag_entity["tags"]) == 0

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/untag",
        headers=normal_user_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/untag",
        headers=normal_user_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404


def test_source_add_remove_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker)
    source1 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source1.id}
    )

    assert r.status_code == 200
    source_entity = r.json()
    assert source_entity is not None
    assert any([i for i in source_entity["sources"] if i["id"] == source1.id])

    source2 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source2.id}
    )

    assert r.status_code == 200
    source_entity = r.json()
    assert source_entity is not None
    assert any([i for i in source_entity["sources"] if i["id"] == source2.id])

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": source1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source1.id},
    )

    assert r.status_code == 200
    source_entity = r.json()
    assert source_entity is not None
    assert any([i for i in source_entity["sources"] if i["id"] != source1.id])

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source2.id},
    )

    assert r.status_code == 200
    source_entity = r.json()
    assert source_entity is not None
    assert len(source_entity["sources"]) == 0

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/remove-source",
        headers=normal_user_token_headers,
        json={"id": source2.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/remove-source",
        headers=normal_user_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404


def test_entities_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity_parent = create_random_entity(db, faker)
    entity = create_random_entity(db, faker, TargetTypeEnum.entity, entity_parent.id)

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity_parent.id}/entity",
        headers=normal_user_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id

    r = client.get(
        f"{settings.API_V1_STR}/entity/-1/entity",
        headers=normal_user_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0


def test_history_entity(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker)

    data = {
        "data_ver": str(faker.pyfloat(2, 3, True))
    }

    r = client.put(
        f"{settings.API_V1_STR}/entity/{entity.id}",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert any(i["audit_data"]["data_ver"] == data["data_ver"] for i in entity_data)
    assert entity_data[0]["audit_data"]["data_ver"] == data["data_ver"]

    r = client.get(
        f"{settings.API_V1_STR}/entity/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data == []


def test_search_entity(client: TestClient, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    entities = []
    for _ in range(5):
        entities.append(create_random_entity(db, faker))

    random_entity = random.choice(entities)

    r = client.get(
        f"{settings.API_V1_STR}/entity/?id={random_entity.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["totalCount"] == 1
    assert r.json()["resultCount"] == 1
    assert r.json()["result"][0]["id"] == random_entity.id

    r = client.get(
        f"{settings.API_V1_STR}/entity/?id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["totalCount"] == 0
    assert r.json()["resultCount"] == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/entity/?id=!{random_entity.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_entity.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/entity/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/entity/?id=({entities[0].id},{entities[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == entities[0].id
    assert r.json()["result"][3]["id"] == entities[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/entity/?id=!({entities[0].id},{entities[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != entities[0].id for a in r.json()["result"])
    assert any(a["id"] != entities[1].id for a in r.json()["result"])
    assert any(a["id"] != entities[2].id for a in r.json()["result"])
    assert any(a["id"] != entities[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/entity/?id=[{entities[0].id},{entities[4].id},{entities[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == entities[0].id
    assert r.json()["result"][1]["id"] == entities[2].id
    assert r.json()["result"][2]["id"] == entities[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/entity/?id=![{entities[0].id},{entities[4].id},{entities[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != entities[0].id for a in r.json()["result"])
    assert all(a["id"] != entities[2].id for a in r.json()["result"])
    assert all(a["id"] != entities[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.entity, random_entity.id)

    r = client.get(
        f"{settings.API_V1_STR}/entity/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_entity.id

    r = client.get(
        f"{settings.API_V1_STR}/entity/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_entity.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.entity, random_entity.id)

    r = client.get(
        f"{settings.API_V1_STR}/entity/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_entity.id

    r = client.get(
        f"{settings.API_V1_STR}/entity/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_entity.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entity/?value={random_entity.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entity.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entity/?type_name={random_entity.type_name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_entity.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entity/?status={random_entity.status.value}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["status"] == random_entity.status.value for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/entity/?status={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422


def test_add_flair_results_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    alert = create_random_alert(db, faker)
    entity = create_random_entity(db, faker, TargetTypeEnum.alert, alert.id)

    data = {
        "targets": [{"type": TargetTypeEnum.alert.value, "id": alert.id}],
        "entities": [{"entity_type": faker.word(), "entity_value": entity.value}]
    }

    r = client.post(
        f"{settings.API_V1_STR}/entity/flair/results",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    assert r.json() is None

    r = client.post(
        f"{settings.API_V1_STR}/entity/flair/results",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_create_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    data = {
        "entity": {
            "entry_count": faker.pyint(1, 20),
            "status": random.choice(list(EntityStatusEnum)).value,
            "value": faker.word(),
            "type_name": faker.word(),
            "data_ver": str(faker.pyfloat(1, 1, True))
        }
    }

    r = client.post(
        f"{settings.API_V1_STR}/entity/",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_entity = r.json()
    assert created_entity["value"] == data["entity"]["value"]
    assert crud.entity.get(db, created_entity["id"]) is not None

    r = client.post(
        f"{settings.API_V1_STR}/entity/",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422


def test_appearances_for_flair_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    entity = create_random_entity(db, faker, TargetTypeEnum.alertgroup, alertgroup.id, pivot=False)

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/flair_appearances",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert "alertgroup_appearances" not in entry_data.keys()
    assert all([len(a) == 0 for a in entry_data.values()])

    entity = create_random_entity(db, faker, pivot=False)
    alerts = []
    for _ in range(11):
        alert = create_random_alert(db, faker)
        link_create = schemas.LinkCreate(
            v1_type=TargetTypeEnum.entity,
            v1_id=entity.id,
            v0_type=TargetTypeEnum.alert,
            v0_id=alert.id
        )
        crud.link.create(db, obj_in=link_create)
        alerts.append(alert)

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/flair_appearances",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert "alert_appearances" in entry_data.keys()
    assert len(entry_data["alert_appearances"]) == 10
    assert entry_data["alert_appearances"][0]["id"] == alerts[-1].id

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/flair_appearances?skip=10",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert "alert_appearances" in entry_data.keys()
    assert len(entry_data["alert_appearances"]) == 1
    assert entry_data["alert_appearances"][0]["id"] == alerts[0].id

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/flair_appearances?limit=1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert "alert_appearances" in entry_data.keys()
    assert len(entry_data["alert_appearances"]) == 1
    assert entry_data["alert_appearances"][0]["id"] == alerts[-1].id

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/flair_appearances?skip=1&limit=1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert "alert_appearances" in entry_data.keys()
    assert len(entry_data["alert_appearances"]) == 1
    assert entry_data["alert_appearances"][0]["id"] == alerts[-2].id


def test_entity_pivots(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity_type = create_random_entity_type(db, faker)
    entity = create_random_entity(db, faker, entity_type_id=entity_type.id, pivot=False)
    pivot = create_random_pivot(db, faker, [entity_type.id])

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/pivot",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["totalCount"] == 1
    assert entity_data["resultCount"] == 1
    assert entity_data["result"][0]["id"] == pivot.id

    r = client.get(
        f"{settings.API_V1_STR}/entity/-1/pivot",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["totalCount"] == 0
    assert entity_data["resultCount"] == 0
    assert len(entity_data["result"]) == 0


def test_entity_enrichments_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker, enrich=True)

    r = client.get(
        f"{settings.API_V1_STR}/entity/{entity.id}/enrichment",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert isinstance(entity_data, dict)
    assert len(entity_data.keys()) != 0

    r = client.get(
        f"{settings.API_V1_STR}/entity/-1/enrichment",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404


def test_entity_class_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker)
    entity_class = create_random_entity_class(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/entity_class",
        headers=normal_user_token_headers,
        json={"entity_class_ids": [entity_class.id]}
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert len(entity_data["classes"]) >= 0
    assert any([i for i in entity_data["classes"] if i["id"] == entity_class.id])

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/entity_class",
        headers=normal_user_token_headers,
        json={"entity_class_ids": [entity_class.id]}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/entity_class",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_add_enrichment_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker)

    enrichment_class = random.choice(list(EnrichmentClassEnum))
    enrichment_data = {}
    if enrichment_class == EnrichmentClassEnum.markdown:
        enrichment_data = {
            "markdown": faker.sentence()
        }
    elif enrichment_class == EnrichmentClassEnum.linechart:
        enrichment_data = {
            "chart_data": {
                "labels": [faker.word() for _ in range(5)],
                "datasets": [faker.word() for _ in range(5)]
            }
        }
    elif enrichment_class == EnrichmentClassEnum.jsontree:
        enrichment_data = faker.pydict(value_types=(str, int, float, bool))
    elif enrichment_class == EnrichmentClassEnum.plaintext:
        enrichment_data = {
            "plaintext": faker.sentence()
        }

    data = {
        "title": faker.word(),
        "entity_id": entity.id,
        "enrichment_class": enrichment_class.value,
        "data": enrichment_data,
        "description": faker.sentence()
    }

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/enrichment",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["id"] == entity.id

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/enrichment",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/enrichment",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404


def test_remove_entity_class_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity_class = create_random_entity_class(db, faker)
    entity = create_random_entity(db, faker, entity_class_ids=[entity_class.id])

    data = {
        "entity_class_ids": [entity_class.id]
    }

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/entity_class/remove",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["id"] == entity.id
    assert entity_data["classes"] == []

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/entity_class/remove",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/entity_class/remove",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422


def test_enrich_entity(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    entity = create_random_entity(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/entity/{entity.id}/enrich_request",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    assert r.json() == {"message": "Enrichment queued"}

    r = client.post(
        f"{settings.API_V1_STR}/entity/-1/enrich_request",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404
