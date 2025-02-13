import os
import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enums import TargetTypeEnum
from tests.utils.file import create_random_file
from tests.utils.user import create_random_user
from tests.utils.tag import create_random_tag
from tests.utils.source import create_random_source


def test_get_file(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    file = create_random_file(db, faker, user)

    r = client.get(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file.owner == file_data["owner"]
    assert file.file_pointer == file_data["file_pointer"]
    assert file.sha256 == file_data["sha256"]

    r = client.get(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/file/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404


def test_put_file(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    file = create_random_file(db, faker, user)
    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file.description != file_data["description"]
    assert file_data["description"] == data["description"]

    r = client.put(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=normal_user_token_headers,
        json=data,
    )

    assert r.status_code == 403

    r = client.put(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.put(
        f"{settings.API_V1_STR}/file/-1",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 404


def test_tag_untag(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = create_random_file(db, faker, owner)
    tag = create_random_tag(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/tag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_file = r.json()
    assert any([i for i in tag_file["tags"] if i["id"] == tag.id])

    tag2 = create_random_tag(db, faker)
    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/tag",
        headers=normal_user_token_headers,
        json={"id": tag2.id}
    )

    assert r.status_code == 200
    tag_file = r.json()
    assert any([i for i in tag_file["tags"] if i["id"] == tag2.id])

    r = client.post(
        f"{settings.API_V1_STR}/file/-1/tag",
        headers=normal_user_token_headers,
        json={"id": tag2.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/tag",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 200
    tag_file = r.json()
    assert any([i for i in tag_file["tags"] if i["id"] != tag.id])

    r = client.post(
        f"{settings.API_V1_STR}/file/-1/untag",
        headers=superuser_token_headers,
        json={"id": tag.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/untag",
        headers=superuser_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422


def test_source_add_remove(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = create_random_file(db, faker, owner)
    source = create_random_source(db, faker)

    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    file_source = r.json()
    assert any([i for i in file_source["sources"] if i["id"] == source.id])

    r = client.post(
        f"{settings.API_V1_STR}/file/-1/add-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/add-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 200
    file_source = r.json()
    assert file_source["sources"] == []

    r = client.post(
        f"{settings.API_V1_STR}/file/-1/remove-source",
        headers=normal_user_token_headers,
        json={"id": source.id}
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/file/{file.id}/remove-source",
        headers=normal_user_token_headers,
        json={"id": -1}
    )

    assert r.status_code == 422


def test_history(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = create_random_file(db, faker, owner)

    data = {
        "description": faker.sentence()
    }

    r = client.put(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=superuser_token_headers,
        json=data,
    )

    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/file/{file.id}/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_data = r.json()
    assert any(i["audit_data"]["description"] == data["description"] for i in file_data)

    r = client.get(
        f"{settings.API_V1_STR}/file/{file.id}/history",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.get(
        f"{settings.API_V1_STR}/file/-1/history",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data == []


def test_create_file(client: TestClient, normal_user_token_headers: dict, faker: Faker) -> None:
    file_data = faker.binary()
    r = client.post(
        f"{settings.API_V1_STR}/file/",
        headers=normal_user_token_headers,
        files={"file": file_data}
    )

    assert r.status_code == 200
    assert r.json() is not None
    file_object = r.json()
    assert file_object["filesize"] == len(file_data)
    file_path = os.path.join(settings.FILE_STORAGE_LOCATION, file_object["file_pointer"])
    assert os.path.exists(file_path)
    saved_file_data = open(file_path, "rb").read()
    assert len(file_data) == len(saved_file_data)
    assert file_data == saved_file_data

    r = client.post(
        f"{settings.API_V1_STR}/file/",
        headers=normal_user_token_headers
    )

    assert r.status_code == 422


def test_download_file(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = create_random_file(db, faker, owner)

    r = client.get(
        f"{settings.API_V1_STR}/file/download/{file.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    file_data = b""
    for data in r.stream:
        file_data += data
    local_file_data = open(os.path.join(settings.FILE_STORAGE_LOCATION, file.file_pointer), "rb").read()
    assert file_data == local_file_data

    r = client.get(
        f"{settings.API_V1_STR}/file/download/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404


def test_delete_files(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = create_random_file(db, faker, owner)

    r = client.delete(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/file/-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_delete = r.json()
    assert file_delete["id"] == file.id
    original_file_path = os.path.join(settings.FILE_STORAGE_LOCATION, file.file_pointer)
    assert not os.path.exists(original_file_path)
    delete_file_path = os.path.join(settings.FILE_DELETED_LOCATION, file.file_pointer)
    assert os.path.exists(delete_file_path)

    r = client.get(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 404


def test_search_files(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    files = []
    for _ in range(5):
        files.append(create_random_file(db, faker, owner))

    r = client.get(
        f"{settings.API_V1_STR}/file/?owner={owner.username}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data["totalCount"] == len(files)
    assert file_data["resultCount"] == len(files)
    assert (x["id"] == files[0].id for x in file_data["result"])

    random_file = random.choice(files)
    r = client.get(
        f"{settings.API_V1_STR}/file/?id={random_file.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data["totalCount"] == 1
    assert file_data["resultCount"] == 1
    assert file_data["result"][0]["id"] == random_file.id

    r = client.get(
        f"{settings.API_V1_STR}/file/?id={random_file.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    file_data = r.json()
    assert file_data["totalCount"] == 0
    assert file_data["resultCount"] == 0
    assert len(file_data["result"]) == 0

    # int negations
    r = client.get(
        f"{settings.API_V1_STR}/file/?id=!{random_file.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != random_file.id for a in r.json()["result"])

    # test type checking
    r = client.get(
        f"{settings.API_V1_STR}/file/?id={faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    # id range
    r = client.get(
        f"{settings.API_V1_STR}/file/?id=({files[0].id},{files[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert r.json()["result"][0]["id"] == files[0].id
    assert r.json()["result"][3]["id"] == files[3].id

    # not id range
    r = client.get(
        f"{settings.API_V1_STR}/file/?id=!({files[0].id},{files[3].id})",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(a["id"] != files[0].id for a in r.json()["result"])
    assert any(a["id"] != files[1].id for a in r.json()["result"])
    assert any(a["id"] != files[2].id for a in r.json()["result"])
    assert any(a["id"] != files[3].id for a in r.json()["result"])

    # id in list
    r = client.get(
        f"{settings.API_V1_STR}/file/?id=[{files[0].id},{files[4].id},{files[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 3
    assert r.json()["result"][0]["id"] == files[0].id
    assert r.json()["result"][1]["id"] == files[2].id
    assert r.json()["result"][2]["id"] == files[4].id

    # id not in list
    r = client.get(
        f"{settings.API_V1_STR}/file/?id=![{files[0].id},{files[4].id},{files[2].id}]",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(a["id"] != files[0].id for a in r.json()["result"])
    assert all(a["id"] != files[2].id for a in r.json()["result"])
    assert all(a["id"] != files[4].id for a in r.json()["result"])

    # type checking
    tag = create_random_tag(db, faker, TargetTypeEnum.file, random_file.id)

    r = client.get(
        f"{settings.API_V1_STR}/file/?tag={tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert len(r.json()["result"]) == 1
    assert r.json()["result"][0]["id"] == random_file.id

    r = client.get(
        f"{settings.API_V1_STR}/file/?tag=!{tag.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_file.id for i in r.json()["result"])

    source = create_random_source(db, faker, TargetTypeEnum.file, random_file.id)

    r = client.get(
        f"{settings.API_V1_STR}/file/?source={source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_file.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/file/?source=!{source.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["id"] != random_file.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/file/?tlp={random_file.tlp.name}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_file.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/file/?tlp={faker.word()}_{faker.word()}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.get(
        f"{settings.API_V1_STR}/file/?filename={random_file.filename}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_file.id for i in r.json()["result"])

    glob_filename = f"*{random_file.filename[faker.pyint(1, 3):faker.pyint(-3, -1)]}%"
    r = client.get(
        f"{settings.API_V1_STR}/file/?glob={glob_filename}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["filename"] == random_file.filename for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/file/?sha256={random_file.sha256}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_file.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/file/?description={random_file.description[1:-1]}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert any(i["id"] == random_file.id for i in r.json()["result"])

    r = client.get(
        f"{settings.API_V1_STR}/file/?content_type={random_file.content_type}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    assert all(i["content_type"] == random_file.content_type for i in r.json()["result"])


def test_undelete(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    file = create_random_file(db, faker, owner)

    r = client.delete(
        f"{settings.API_V1_STR}/file/{file.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200

    r = client.post(
        f"{settings.API_V1_STR}/file/undelete?target_id={file.id}",
        headers=normal_user_token_headers
    )
  
    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/file/undelete?target_id=-1",
        headers=superuser_token_headers
    )

    assert r.status_code == 404

    r = client.post(
        f"{settings.API_V1_STR}/file/undelete?target_id={file.id}",
        headers=superuser_token_headers
    )

    assert r.status_code == 200
    file_undelete = r.json()
    assert file_undelete["id"] == file.id
    original_file_path = os.path.join(settings.FILE_STORAGE_LOCATION, file_undelete["file_pointer"])
    assert os.path.exists(original_file_path)
    delete_file_path = os.path.join(settings.FILE_DELETED_LOCATION, file_undelete["file_pointer"])
    assert not os.path.exists(delete_file_path)
