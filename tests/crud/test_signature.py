import random
import json
from faker import Faker
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Signature
from app.schemas.signature import SignatureCreate, SignatureUpdate

from tests.utils.alert import create_random_alert
from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.signature import create_random_signature
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role
from tests.utils.link import create_link
from tests.utils.event import create_random_event


def test_get_signature(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    db_obj = crud.signature.get(db, signature.id)

    assert db_obj.id == signature.id

    db_obj = crud.signature.get(db, -1)

    assert db_obj is None


def test_get_multi_signature(db: Session, faker: Faker) -> None:
    signatures = []
    for _ in range(5):
        signatures.append(create_random_signature(db, faker))

    db_objs = crud.signature.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == signatures[0].id for i in db_objs)

    db_objs = crud.signature.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == signatures[1].id for i in db_objs)

    db_objs = crud.signature.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.signature.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_signature(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = SignatureCreate(
        owner=owner.username,
        name=faker.word(),
        description=faker.text(max_nb_chars=30),
        data=jsonable_encoder(faker.pydict()),
        type=faker.word(),
    )
    db_obj = crud.signature.create(db, obj_in=signature)

    assert db_obj.id is not None
    assert db_obj.owner == signature.owner
    assert db_obj.name == signature.name
    assert db_obj.description == signature.description
    assert db_obj.data == signature.data
    assert db_obj.type == signature.type


def test_update_signature(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    owner = create_random_user(db, faker)
    update = SignatureUpdate(
        owner=owner.username,
        name=faker.word(),
        description=faker.text(max_nb_chars=30),
        data=jsonable_encoder(faker.pydict()),
        type=faker.word(),
    )

    db_obj = crud.signature.update(db, db_obj=signature, obj_in=update)

    assert db_obj.id == signature.id
    assert db_obj.owner == update.owner
    assert db_obj.name == update.name
    assert db_obj.description == update.description
    assert db_obj.data == update.data
    assert db_obj.type == update.type

    update = {}

    db_obj = crud.signature.update(db, db_obj=signature, obj_in=update)

    assert db_obj.id == signature.id

    update = {
        "test": "test"
    }

    db_obj = crud.signature.update(db, db_obj=signature, obj_in=update)

    assert db_obj.id == signature.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "name": faker.word(),
        "description": faker.text(max_nb_chars=30),
        "data": jsonable_encoder(faker.pydict()),
        "type": faker.word(),
    }

    db_obj = crud.signature.update(db, db_obj=Signature(), obj_in=update)

    assert db_obj.id == signature.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.name == update["name"]
    assert db_obj.description == update["description"]
    assert db_obj.data == update["data"]
    assert db_obj.type == update["type"]


def test_remove_signature(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)

    db_obj = crud.signature.remove(db, _id=signature.id)

    assert db_obj.id == signature.id

    db_obj_del = crud.signature.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.signature.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_signature(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = SignatureCreate(
        owner=owner.username,
        name=faker.word(),
        description=faker.text(max_nb_chars=30),
        data=jsonable_encoder(faker.pydict()),
        type=faker.word(),
    )

    db_obj = crud.signature.get_or_create(db, obj_in=signature)

    assert db_obj.id is not None

    same_db_obj = crud.signature.get_or_create(db, obj_in=signature)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_signature(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signatures = []
    for _ in range(5):
        signatures.append(create_random_signature(db, faker, owner.username))

    random_signature = random.choice(signatures)

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"id": random_signature.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_signature.id

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(signatures)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(signatures) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"name": random_signature.name})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0].id == random_signature.id

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"description": random_signature.description})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0].id == random_signature.id

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"name": f"!{random_signature.name}"})

    assert db_obj is not None
    assert all(a.name != random_signature.name for a in db_obj)

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"description": f"!{random_signature.description}"})

    assert db_obj is not None
    assert all(a.description != random_signature.description for a in db_obj)

    db_obj, count = crud.signature.query_with_filters(db, filter_dict={"signature_group": f"!{list(random_signature.data.keys())[0]}"})

    assert db_obj is not None
    assert all(random_signature.data.keys()[0] in json.loads(a.data) for a in db_obj)


def test_get_with_roles_signature(db: Session, faker: Faker) -> None:
    signatures = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        signature = SignatureCreate(
            owner=owner.username,
            name=faker.word(),
            description=faker.text(max_nb_chars=30),
            data=jsonable_encoder(faker.pydict()),
            type=faker.word(),
        )
        roles.append(role)

        signatures.append(crud.signature.create_with_permissions(db, obj_in=signature, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.signature.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_signature(db: Session, faker: Faker) -> None:
    signatures = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        signature = SignatureCreate(
            owner=owner.username,
            name=faker.word(),
            description=faker.text(max_nb_chars=30),
            data=jsonable_encoder(faker.pydict()),
            type=faker.word(),
        )
        roles.append(role)

        signatures.append(crud.signature.create_with_permissions(db, obj_in=signature, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.signature.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_signature(db: Session, faker: Faker) -> None:
    signature = SignatureCreate(
        name=faker.word(),
        description=faker.text(max_nb_chars=30),
        data=jsonable_encoder(faker.pydict()),
        type=faker.word(),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.signature.create_with_owner(db, obj_in=signature, owner=owner)

    assert db_obj is not None
    assert db_obj.name == signature.name
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_signature(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    signature = SignatureCreate(
        owner=owner.username,
        name=faker.word(),
        description=faker.text(max_nb_chars=30),
        data=jsonable_encoder(faker.pydict()),
        type=faker.word(),
    )

    db_obj = crud.signature.create_with_permissions(db, obj_in=signature, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == signature.owner
    assert db_obj.name == signature.name
    assert db_obj.description == signature.description
    assert db_obj.data == signature.data
    assert db_obj.type == signature.type

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.signature, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_signature(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = SignatureCreate(
        owner=owner.username,
        name=faker.word(),
        description=faker.text(max_nb_chars=30),
        data=jsonable_encoder(faker.pydict()),
        type=faker.word(),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.signature.create_in_object(db, obj_in=signature, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.name == signature.name

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v0_target": TargetTypeEnum.alertgroup, "v1_id": db_obj.id, "v1_target": TargetTypeEnum.signature})

    assert count >= 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_signature(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = SignatureCreate(
        owner=owner.username,
        name=faker.word(),
        description=faker.text(max_nb_chars=30),
        data=jsonable_encoder(faker.pydict()),
        type=faker.word(),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.signature.create(db, obj_in=signature, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.signature.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_signature(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker, user.username)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.signature.remove(db, _id=signature.id, audit_logger=audit_logger)

    assert db_obj.id == signature.id

    db_obj = crud.signature.undelete(db, db_obj.id)

    assert db_obj is None


def test_retrieve_signature_links(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    alert = create_random_alert(db, faker)
    create_link(db, faker, TargetTypeEnum.signature, signature.id, TargetTypeEnum.alert, alert.id)

    db_obj, count = crud.signature.retrieve_signature_links(db, signature.id)

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0]["type"] == TargetTypeEnum.alert
    assert db_obj[0]["id"] == alert.id


def test_get_event_owner_stats(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    event = create_random_event(db, faker, user.username, False)
    signature = create_random_signature(db, faker, user.username)
    create_link(db, faker, TargetTypeEnum.signature, signature.id, TargetTypeEnum.event, event.id)

    db_obj = crud.signature.get_event_owner_stats(db, signature.id)

    assert len(db_obj) == 1
    assert db_obj[0]["owner"] == user.username
    assert db_obj[0]["count"] == 1
