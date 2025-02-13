import random

from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app import crud
from utils.appearance import create_random_appearance
from utils.audit import create_audit


def test_read_audit(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, faker: Faker, db: Session) -> None:
    normal_user = crud.user.get_by_username(db, username=settings.EMAIL_TEST_USER)
    super_user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    db_obj = create_random_appearance(db, faker)
    # create audit with normal user
    normal_audit = create_audit(
        db,
        faker,
        normal_user,
        db_obj,
        client.base_url,
        client.headers.get("user-agent", None),
    )
    super_audit = create_audit(
        db,
        faker,
        super_user,
        db_obj,
        client.base_url,
        client.headers.get("user-agent", None),
    )

    # test get normal user audit
    r = client.get(
        f"{settings.API_V1_STR}/audit/{normal_audit.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    # test get super user audit
    r = client.get(
        f"{settings.API_V1_STR}/audit/{super_audit.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    get_audit = r.json()
    assert get_audit is not None
    assert get_audit["id"] == super_audit.id

    # test get super user audit as normal user
    r = client.get(
        f"{settings.API_V1_STR}/audit/{super_audit.id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    # test get normal user audit as super user
    r = client.get(
        f"{settings.API_V1_STR}/audit/{normal_audit.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    get_audit = r.json()
    assert get_audit is not None
    assert get_audit["id"] == normal_audit.id

    r = client.get(
        f"{settings.API_V1_STR}/audit/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/audit/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403


def test_search_audit(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    audits = []
    super_user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    for _ in range(5):
        db_obj = create_random_appearance(db, faker)
        audits.append(
            create_audit(
                db,
                faker,
                super_user,
                db_obj,
                client.base_url,
                client.headers.get("user-agent", None),
            )
        )

    audit = random.choice(audits)
    r = client.get(
        f"{settings.API_V1_STR}/audit/?id={audit.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    searched_audit = r.json()
    assert searched_audit is not None
    assert searched_audit["totalCount"] == 1
    assert searched_audit["resultCount"] == 1
    assert searched_audit["result"][0]["id"] == audit.id

    r = client.get(
        f"{settings.API_V1_STR}/audit/?username={audit.username}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    searched_audit = r.json()
    assert searched_audit is not None
    assert searched_audit["totalCount"] >= 5
    assert searched_audit["resultCount"] >= 5
    assert any([i for i in searched_audit["result"] if i["username"] == audit.username])

    r = client.get(
        f"{settings.API_V1_STR}/audit/?id=-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    searched_audit = r.json()
    assert searched_audit is not None
    assert searched_audit["totalCount"] == 0
    assert searched_audit["resultCount"] == 0
    assert searched_audit["result"] == []

    r = client.get(
        f"{settings.API_V1_STR}/audit/?id=-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    searched_audit = r.json()
    assert searched_audit is not None
    assert searched_audit["totalCount"] == 0
    assert searched_audit["resultCount"] == 0
    assert searched_audit["result"] == []


def test_delete_audit(client: TestClient, normal_user_token_headers: dict, superuser_token_headers: dict, db: Session, faker: Faker) -> None:
    super_user = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    db_obj = create_random_appearance(db, faker)
    super_audit = create_audit(
        db,
        faker,
        super_user,
        db_obj,
        client.base_url,
        client.headers.get("user-agent", None)
    )

    r = client.delete(
        f"{settings.API_V1_STR}/audit/{super_audit.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 200
    deleted_audit = r.json()
    assert deleted_audit is not None
    assert deleted_audit["id"] == super_audit.id

    r = client.get(
        f"{settings.API_V1_STR}/audit/{super_audit.id}",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/audit/-1",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 403

    r = client.delete(
        f"{settings.API_V1_STR}/audit/-1",
        headers=superuser_token_headers,
    )

    assert r.status_code == 404
