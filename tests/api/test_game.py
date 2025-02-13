from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

from tests.utils.game import create_random_game
from tests.utils.audit import create_audit
from tests.utils.alert import create_random_alert
from tests.utils.user import create_random_user


def test_get_games(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/game",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    game_data = r.json()
    assert game_data is not None
    assert len(game_data) == 0

    games = []
    for _ in range(3):
        user = create_random_user(db, faker)
        alert = create_random_alert(db, faker, user)
        audit = create_audit(db, faker, user, alert)
        games.append(create_random_game(db, faker, audit))

    r = client.get(
        f"{settings.API_V1_STR}/game",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    game_data = r.json()
    assert game_data is not None
    assert len(game_data) == len(games)
    assert any(i["id"] == games[0].id for i in game_data)


def test_create_game(client: TestClient, superuser_token_headers: dict, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)

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
        f"{settings.API_V1_STR}/game",
        headers=normal_user_token_headers,
        json=data
    )

    assert r.status_code == 403

    r = client.post(
        f"{settings.API_V1_STR}/game",
        headers=superuser_token_headers,
    )

    assert r.status_code == 422

    r = client.post(
        f"{settings.API_V1_STR}/game",
        headers=superuser_token_headers,
        json=data
    )

    assert r.status_code == 200
    game_data = r.json()
    assert game_data is not None
    assert game_data["id"] > 0
    assert game_data["name"] == data["name"]


def test_get_results(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)
    game = create_random_game(db, faker, audit)

    r = client.get(
        f"{settings.API_V1_STR}/game/results",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    game_data = r.json()
    assert game_data is not None
    assert any(i["name"] == game.name for i in game_data)


def test_get_game(client: TestClient, normal_user_token_headers: dict, db: Session, faker: Faker) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/game/-1",
        headers=normal_user_token_headers
    )

    assert r.status_code == 404

    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)
    game = create_random_game(db, faker, audit)

    r = client.get(
        f"{settings.API_V1_STR}/game/{game.id}",
        headers=normal_user_token_headers
    )

    assert r.status_code == 200
    game_data = r.json()
    assert game_data is not None
    assert game.id == game_data["id"]
