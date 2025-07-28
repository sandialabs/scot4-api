import random
from datetime import timedelta
from faker import Faker
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Game
from app.schemas.game import GameCreate, GameUpdate

from tests.utils.alert import create_random_alert
from tests.utils.audit import create_audit
from tests.utils.game import create_random_game
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_game(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)
    game = create_random_game(db, faker, audit)
    db_obj = crud.game.get(db, game.id)

    assert db_obj.id == game.id

    db_obj = crud.game.get(db, -1)

    assert db_obj is None


def test_get_multi_game(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    games = []
    for _ in range(5):
        audit = create_audit(db, faker, user, alert)
        games.append(create_random_game(db, faker, audit))

    db_objs = crud.game.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == games[0].id for i in db_objs)

    db_objs = crud.game.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == games[1].id for i in db_objs)

    db_objs = crud.game.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.game.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_game(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)
    game = GameCreate(
        name=faker.word(),
        tooltip=faker.sentence(),
        parameters={
            "what": audit.what,
            "type": audit.thing_type,
            "id": audit.thing_id,
            "data": jsonable_encoder(audit.audit_data)
        }
    )
    db_obj = crud.game.create(db, obj_in=game)

    assert db_obj.id is not None
    assert db_obj.name == game.name
    assert db_obj.tooltip == game.tooltip
    assert db_obj.parameters == game.parameters


def test_update_game(db: Session, faker: Faker) -> None:
    game = create_random_game(db, faker)
    owner = create_random_user(db, faker)
    alert = create_random_alert(db, faker, owner)
    audit = create_audit(db, faker, owner, alert)
    update = GameUpdate(
        name=faker.word(),
        tooltip=faker.sentence(),
        parameters={
            "what": audit.what,
            "type": audit.thing_type,
            "id": audit.thing_id,
            "data": jsonable_encoder(audit.audit_data)
        }
    )

    db_obj = crud.game.update(db, db_obj=game, obj_in=update)

    assert db_obj.id == game.id
    assert db_obj.name == update.name
    assert db_obj.tooltip == update.tooltip

    update = {}

    db_obj = crud.game.update(db, db_obj=game, obj_in=update)

    assert db_obj.id == game.id

    update = {
        "test": "test"
    }

    db_obj = crud.game.update(db, db_obj=game, obj_in=update)

    assert db_obj.id == game.id
    assert not hasattr(db_obj, "test")

    update = {
        "name": faker.word(),
        "tooltip": faker.sentence(),
    }

    db_obj = crud.game.update(db, db_obj=Game(), obj_in=update)

    assert db_obj.id == game.id + 1
    assert db_obj.name == update["name"]
    assert db_obj.tooltip == update["tooltip"]


def test_remove_game(db: Session, faker: Faker) -> None:
    game = create_random_game(db, faker)

    db_obj = crud.game.remove(db, _id=game.id)

    assert db_obj.id == game.id

    db_obj_del = crud.game.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.game.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_game(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)
    game = GameCreate(
        name=faker.word(),
        tooltip=faker.sentence(),
        parameters={
            "what": audit.what,
            "type": audit.thing_type,
            "id": audit.thing_id,
            "data": jsonable_encoder(audit.audit_data)
        }
    )

    db_obj = crud.game.get_or_create(db, obj_in=game)

    assert db_obj.id is not None

    same_db_obj = crud.game.get_or_create(db, obj_in=game)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_game(db: Session, faker: Faker) -> None:
    schemas = []
    for _ in range(5):
        schemas.append(create_random_game(db, faker))

    random_schema = random.choice(schemas)

    db_obj, count = crud.game.query_with_filters(db, filter_dict={"id": random_schema.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_schema.id

    db_obj, count = crud.game.query_with_filters(db, filter_dict={"name": f"!{random_schema.name}"})

    assert db_obj is not None
    assert all(a.name != random_schema.name for a in db_obj)


def test_get_with_roles_game(db: Session, faker: Faker) -> None:
    schemas = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        alert = create_random_alert(db, faker, owner)
        audit = create_audit(db, faker, owner, alert)
        game = GameCreate(
            name=faker.word(),
            tooltip=faker.sentence(),
            parameters={
                "what": audit.what,
                "type": audit.thing_type,
                "id": audit.thing_id,
                "data": jsonable_encoder(audit.audit_data)
            }
        )
        roles.append(role)

        schemas.append(crud.game.create_with_permissions(db, obj_in=game, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.game.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_game(db: Session, faker: Faker) -> None:
    schemas = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        alert = create_random_alert(db, faker)
        audit = create_audit(db, faker, owner, alert)
        game = GameCreate(
            name=faker.word(),
            tooltip=faker.sentence(),
            parameters={
                "what": audit.what,
                "type": audit.thing_type,
                "id": audit.thing_id,
                "data": jsonable_encoder(audit.audit_data)
            }
        )
        roles.append(role)

        schemas.append(crud.game.create_with_permissions(db, obj_in=game, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.game.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_game(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)
    game = GameCreate(
        name=faker.word(),
        tooltip=faker.sentence(),
        parameters={
            "what": audit.what,
            "type": audit.thing_type,
            "id": audit.thing_id,
            "data": jsonable_encoder(audit.audit_data)
        }
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.game.create_with_owner(db, obj_in=game, owner=owner)

    assert db_obj is not None
    assert db_obj.name == game.name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_game(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    role = create_random_role(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)
    game = GameCreate(
        name=faker.word(),
        tooltip=faker.sentence(),
        parameters={
            "what": audit.what,
            "type": audit.thing_type,
            "id": audit.thing_id,
            "data": jsonable_encoder(audit.audit_data)
        }
    )

    db_obj = crud.game.create_with_permissions(db, obj_in=game, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.name == game.name
    assert db_obj.tooltip == game.tooltip
    assert db_obj.parameters == game.parameters

    # no permission could be created with appearances so nothing should be returned
    db_obj, count = crud.permission.query_with_filters(db, filter_dict={"target_id": db_obj.id, "target_type": TargetTypeEnum.none})

    assert db_obj == []
    assert count == 0


def test_get_history_game(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    alert = create_random_alert(db, faker, user)
    audit = create_audit(db, faker, user, alert)
    game = GameCreate(
        name=faker.word(),
        tooltip=faker.sentence(),
        parameters={
            "what": audit.what,
            "type": audit.thing_type,
            "id": audit.thing_id,
            "data": jsonable_encoder(audit.audit_data)
        }
    )
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.game.create(db, obj_in=game, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.game.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_game(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    game = create_random_game(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.game.remove(db, _id=game.id, audit_logger=audit_logger)

    assert db_obj.id == game.id

    db_obj = crud.game.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_results_for_games(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alert = create_random_alert(db, faker, owner)
    audit = create_audit(db, faker, owner, alert)
    game = create_random_game(db, faker, audit)

    db_obj = crud.game.get_results_for_games(db)

    assert db_obj is not None
    assert len(db_obj) >= 1

    db_obj = crud.game.get_results_for_games(db, [game.id])

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0]["name"] == game.name
    assert db_obj[0]["tooltip"] == game.tooltip

    audit_data = crud.audit.get(db, audit.id)

    before_date = audit_data.when_date - timedelta(minutes=1)
    after_date = audit_data.when_date + timedelta(minutes=1)
    db_obj = crud.game.get_results_for_games(db, date_range=[before_date, after_date])

    assert db_obj is not None
    assert any(i["name"] == game.name and i["tooltip"] == game.tooltip for i in db_obj)

    db_obj = crud.game.get_results_for_games(db, num_top_users=1)

    assert db_obj is not None
    assert len(db_obj[0]["results"]) == 1
