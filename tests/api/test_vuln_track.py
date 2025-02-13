import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TlpEnum, StatusEnum, TargetTypeEnum, EntryClassEnum

from tests.utils.vuln_track import create_random_vuln_track
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source
from tests.utils.entity import create_random_entity
from tests.utils.entry import create_random_entry
from tests.utils.file import create_random_file
from tests.utils.promotion import promote_vuln_track_to_incident


def test_get_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_track_data = r.json()
    assert vuln_track_data["id"] == vuln_track.id

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/-1",
        headers=superuser_token_headers
    )
    assert r.status_code == 404


def test_create_vuln_track(client: TestClient, normal_user_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    data = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)).value,
        "status": random.choice(list(StatusEnum)).value,
        "subject": faker.sentence(),
        "view_count": faker.pyint()
    }

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 200
    created_vuln_track = r.json()
    assert created_vuln_track["id"] >= 0
    assert created_vuln_track["owner"] == data["owner"]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 422


def test_update_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/vuln_track/-1",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 404

    r = client.put(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    vuln_track_data = r.json()
    assert vuln_track_data["id"] == vuln_track.id
    assert vuln_track_data["subject"] == data["subject"]
    assert vuln_track_data["subject"] != vuln_track.subject


def test_delete_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner, False)

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_track_data = r.json()
    assert vuln_track_data["id"] == vuln_track.id

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_track/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_undelete_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner, False)

    r = client.delete(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/undelete?target_id={vuln_track.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/undelete?target_id={vuln_track.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    delete_vuln_track = r.json()
    assert delete_vuln_track is not None
    assert delete_vuln_track["id"] == vuln_track.id

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/undelete?target_id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_entries_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner, False)
    entry = create_random_entry(db, faker, owner, target_type=TargetTypeEnum.vuln_track, target_id=vuln_track.id, entry_class=EntryClassEnum.entry)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/entry",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/-1/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 0
    assert entry_data["totalCount"] == 0
    assert len(entry_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/entry",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    entry_data = r.json()
    assert entry_data is not None
    assert entry_data["resultCount"] == 1
    assert entry_data["totalCount"] == 1
    assert entry_data["result"][0]["id"] == entry.id


def test_tag_untag_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner, False)
    tag1 = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag1.id}
    )

    assert r.status_code == 200
    tag_vuln_track = r.json()
    assert tag_vuln_track is not None
    assert any([i for i in tag_vuln_track["tags"] if i["id"] == tag1.id])

    tag2 = create_random_tag(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag2.id}
    )

    assert r.status_code == 200
    tag_vuln_track = r.json()
    assert tag_vuln_track is not None
    assert any([i for i in tag_vuln_track["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/-1/tag",
        headers=superuser_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/tag",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/untag",
        headers=normal_user_token_headers,
        json={"id": tag1.id},
    )

    assert r.status_code == 200
    tag_vuln_track = r.json()
    assert tag_vuln_track is not None
    assert any([i for i in tag_vuln_track["tags"] if i["id"] != tag1.id])

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 200
    tag_vuln_track = r.json()
    assert tag_vuln_track is not None
    assert len([i for i in tag_vuln_track["tags"] if i["id"] != tag2.id]) == 0

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag2.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/untag",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 422


def test_source_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner, False)
    source1 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source1.id}
    )

    assert r.status_code == 200
    source_vuln_track = r.json()
    assert source_vuln_track is not None
    assert source1.id in [i["id"] for i in source_vuln_track["sources"]]

    source2 = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/add-source",
        headers=superuser_token_headers,
        json={"id": source2.id}
    )

    assert r.status_code == 200
    source_vuln_track = r.json()
    assert source_vuln_track is not None
    assert source2.id in [i["id"] for i in source_vuln_track["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/-1/add-source",
        headers=superuser_token_headers,
        json={"id": source1.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/add-source",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source1.id},
    )

    assert r.status_code == 200
    source_vuln_track = r.json()
    assert source_vuln_track is not None
    assert source1.id not in [i["id"] for i in source_vuln_track["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": source2.id},
    )

    assert r.status_code == 200
    source_vuln_track = r.json()
    assert source_vuln_track is not None
    assert source2.id not in [i["id"] for i in source_vuln_track["sources"]]

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/-1/remove-source",
        headers=superuser_token_headers,
        json={"id": source2.id},
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/remove-source",
        headers=superuser_token_headers,
        json={"id": -1},
    )

    assert r.status_code == 422


def test_entities_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner, False)
    entity = create_random_entity(db, faker, TargetTypeEnum.vuln_track, vuln_track.id)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/entity",
        headers=normal_user_token_headers
    )
    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/-1/entity",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 0
    assert entity_data["totalCount"] == 0
    assert len(entity_data["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/entity",
        headers=superuser_token_headers
    )

    assert 200 <= r.status_code < 300
    entity_data = r.json()
    assert entity_data is not None
    assert entity_data["resultCount"] == 1
    assert entity_data["totalCount"] == 1
    assert entity_data["result"][0]["id"] == entity.id


def test_files_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner)
    file = create_random_file(db, faker, owner, TargetTypeEnum.vuln_track, vuln_track.id)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/files",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data is not None
    assert file_data["totalCount"] >= 0
    assert file_data["resultCount"] >= 0
    assert any([i for i in file_data["result"] if i["id"] == file.id])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/files",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/-1/files",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data is not None
    assert file_data["totalCount"] == 0
    assert file_data["resultCount"] == 0
    assert len(file_data["result"]) == 0


def test_history_vuln_track(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, owner, False)

    data = {
        "subject": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_track_data = r.json()
    assert any(i["audit_data"]["subject"] == data["subject"] for i in vuln_track_data)
    assert vuln_track_data[0]["audit_data"]["subject"] == data["subject"]

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/{vuln_track.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    vuln_track_data = r.json()
    assert vuln_track_data == []


def test_search_vuln_track(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    owner = create_random_user(db, faker)

    vuln_tracks = []
    for _ in range(5):
        vuln_tracks.append(create_random_vuln_track(db, faker, owner, False))
    random_vuln_track = random.choice(vuln_tracks)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?id={random_vuln_track.id}",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    search = r.json()
    assert search["totalCount"] == 1
    assert search["resultCount"] == 1
    assert search["result"][0]["id"] == random_vuln_track.id

    # 404 if role doesn't exist
    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?id=-1",
        headers=superuser_token_headers,
    )

    assert 200 <= r.status_code < 300
    search = r.json()
    assert search["totalCount"] == 0
    assert search["resultCount"] == 0
    assert len(search["result"]) == 0

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track?id={random_vuln_track.id}",
        headers=normal_user_token_headers,
    )

    search_result = r.json()
    assert 200 <= r.status_code < 300
    assert search_result["totalCount"] == 0
    assert search_result["resultCount"] == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?id=!{random_vuln_track.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_vuln_track.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?id=({vuln_tracks[0].id},{vuln_tracks[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == vuln_tracks[0].id
    assert r.json()["result"][3]["id"] == vuln_tracks[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?id=!({vuln_tracks[0].id},{vuln_tracks[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != vuln_tracks[0].id for a in r.json()["result"])
    assert any(a["id"] != vuln_tracks[1].id for a in r.json()["result"])
    assert any(a["id"] != vuln_tracks[2].id for a in r.json()["result"])
    assert any(a["id"] != vuln_tracks[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?id=[{vuln_tracks[0].id},{vuln_tracks[4].id},{vuln_tracks[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == vuln_tracks[0].id
    assert r.json()["result"][1]["id"] == vuln_tracks[2].id
    assert r.json()["result"][2]["id"] == vuln_tracks[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?id=![{vuln_tracks[0].id},{vuln_tracks[4].id},{vuln_tracks[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != vuln_tracks[0].id for a in r.json()["result"])
    assert all(a["id"] != vuln_tracks[2].id for a in r.json()["result"])
    assert all(a["id"] != vuln_tracks[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.vuln_track, random_vuln_track.id)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_vuln_track.id

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_vuln_track.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.vuln_track, random_vuln_track.id)

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_vuln_track.id

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_vuln_track.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?subject={random_vuln_track.subject[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_vuln_track.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?view_count={random_vuln_track.view_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_vuln_track.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?view_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?status={random_vuln_track.status.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_vuln_track.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?status={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?entry_count={random_vuln_track.entry_count}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_vuln_track.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?entry_count={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    random_vuln_track = random.choice(vuln_tracks)
    incident = promote_vuln_track_to_incident(db, [random_vuln_track.id])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?promoted_to=incident:{incident.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == random_vuln_track.id

    random_vuln_track1 = random.choice(vuln_tracks)
    promote_vuln_track_to_incident(db, [random_vuln_track1.id])

    r = client.get(
        f"{settings.API_V1_STR}/vuln_track/?promoted_to=!incident:{incident.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    api_dispatch = r.json()
    assert len(api_dispatch["result"]) == 1
    assert api_dispatch["result"][0]["id"] == random_vuln_track1.id
