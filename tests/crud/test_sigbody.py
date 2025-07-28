import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum
from app.models import Sigbody
from app.schemas.sigbody import SigbodyCreate, SigbodyUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.sigbody import create_random_sigbody
from tests.utils.signature import create_random_signature
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_sigbody(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    sigbody = create_random_sigbody(db, faker, signature.id)
    db_obj = crud.sigbody.get(db, sigbody.id)

    assert db_obj.id == sigbody.id

    db_obj = crud.sigbody.get(db, -1)

    assert db_obj is None


def test_get_multi_sigbody(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    sigbodies = []
    for _ in range(5):
        sigbodies.append(create_random_sigbody(db, faker, signature.id))

    db_objs = crud.sigbody.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == sigbodies[0].id for i in db_objs)

    db_objs = crud.sigbody.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == sigbodies[1].id for i in db_objs)

    db_objs = crud.sigbody.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.sigbody.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_sigbody(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = SigbodyCreate(
        revision=faker.pyint(),
        body=faker.sentence(),
        body64=faker.sentence(),
        signature_id=signature.id
    )
    db_obj = crud.sigbody.create(db, obj_in=sigbody)

    assert db_obj.id is not None
    assert db_obj.revision == sigbody.revision
    assert db_obj.body == sigbody.body
    assert db_obj.body64 == sigbody.body64
    assert db_obj.signature_id == sigbody.signature_id


def test_update_sigbody(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = create_random_sigbody(db, faker, signature.id)
    update = SigbodyUpdate(
        revision=faker.pyint(),
        body=faker.sentence(),
        body64=faker.sentence(),
        signature_id=signature.id
    )

    db_obj = crud.sigbody.update(db, db_obj=sigbody, obj_in=update)

    assert db_obj.id == sigbody.id
    assert db_obj.revision == update.revision
    assert db_obj.body == update.body
    assert db_obj.body64 == update.body64
    assert db_obj.signature_id == update.signature_id

    update = {}

    db_obj = crud.sigbody.update(db, db_obj=sigbody, obj_in=update)

    assert db_obj.id == sigbody.id

    update = {
        "test": "test"
    }

    db_obj = crud.sigbody.update(db, db_obj=sigbody, obj_in=update)

    assert db_obj.id == sigbody.id
    assert not hasattr(db_obj, "test")

    update = {
        "revision": faker.pyint(),
        "body": faker.sentence(),
        "body64": faker.sentence(),
        "signature_id": signature.id
    }

    db_obj = crud.sigbody.update(db, db_obj=Sigbody(), obj_in=update)

    assert db_obj.id == sigbody.id + 1
    assert db_obj.revision == update["revision"]
    assert db_obj.body == update["body"]
    assert db_obj.body64 == update["body64"]
    assert db_obj.signature_id == update["signature_id"]


def test_remove_sigbody(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    sigbody = create_random_sigbody(db, faker, signature.id)

    db_obj = crud.sigbody.remove(db, _id=sigbody.id)

    assert db_obj.id == sigbody.id

    db_obj_del = crud.sigbody.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.sigbody.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_sigbody(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = SigbodyCreate(
        revision=faker.pyint(),
        body=faker.sentence(),
        body64=faker.sentence(),
        signature_id=signature.id
    )

    db_obj = crud.sigbody.get_or_create(db, obj_in=sigbody)

    assert db_obj.id is not None

    same_db_obj = crud.sigbody.get_or_create(db, obj_in=sigbody)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_sigbody(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    sigbodies = []
    for _ in range(5):
        sigbodies.append(create_random_sigbody(db, faker, signature.id))

    random_sigbody = random.choice(sigbodies)

    db_obj, count = crud.sigbody.query_with_filters(db, filter_dict={"id": random_sigbody.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_sigbody.id

    db_obj, count = crud.sigbody.query_with_filters(db, filter_dict={"signature_id": signature.id})

    assert db_obj is not None
    assert len(db_obj) == len(sigbodies)
    assert len(db_obj) == count
    assert all(a.signature_id == signature.id for a in db_obj)

    db_obj, count = crud.sigbody.query_with_filters(db, filter_dict={"signature_id": signature.id}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(sigbodies) - 1
    assert len(db_obj) == count - 1
    assert all(a.signature_id == signature.id for a in db_obj)

    db_obj, count = crud.sigbody.query_with_filters(db, filter_dict={"signature_id": signature.id}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.signature_id == signature.id for a in db_obj)

    db_obj, count = crud.sigbody.query_with_filters(db, filter_dict={"body": f"!{random_sigbody.body}"})

    assert db_obj is not None
    assert all(a.body != random_sigbody.body for a in db_obj)


def test_get_with_roles_sigbody(db: Session, faker: Faker) -> None:
    sigbodies = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        signature = create_random_signature(db, faker, owner)
        sigbody = SigbodyCreate(
            revision=faker.pyint(),
            body=faker.sentence(),
            body64=faker.sentence(),
            signature_id=signature.id
        )
        roles.append(role)

        sigbodies.append(crud.sigbody.create_with_permissions(db, obj_in=sigbody, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.sigbody.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_sigbody(db: Session, faker: Faker) -> None:
    sigbodies = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        signature = create_random_signature(db, faker, owner)
        sigbody = SigbodyCreate(
            revision=faker.pyint(),
            body=faker.sentence(),
            body64=faker.sentence(),
            signature_id=signature.id
        )
        roles.append(role)

        sigbodies.append(crud.sigbody.create_with_permissions(db, obj_in=sigbody, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.sigbody.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_sigbody(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    sigbody = SigbodyCreate(
        revision=faker.pyint(),
        body=faker.sentence(),
        body64=faker.sentence(),
        signature_id=signature.id
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.sigbody.create_with_owner(db, obj_in=sigbody, owner=owner)

    assert db_obj is not None
    assert db_obj.revision == sigbody.revision
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_sigbody(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = SigbodyCreate(
        revision=faker.pyint(),
        body=faker.sentence(),
        body64=faker.sentence(),
        signature_id=signature.id
    )

    db_obj = crud.sigbody.create_with_permissions(db, obj_in=sigbody, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.revision == sigbody.revision
    assert db_obj.body == sigbody.body
    assert db_obj.body64 == sigbody.body64
    assert db_obj.signature_id == sigbody.signature_id

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.sigbody, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_sigbody(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = SigbodyCreate(
        revision=faker.pyint(),
        body=faker.sentence(),
        body64=faker.sentence(),
        signature_id=signature.id
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.sigbody.create_in_object(db, obj_in=sigbody, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.revision == sigbody.revision

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_sigbody(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    signature = create_random_signature(db, faker, owner)
    sigbody = SigbodyCreate(
        revision=faker.pyint(),
        body=faker.sentence(),
        body64=faker.sentence(),
        signature_id=signature.id
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.sigbody.create(db, obj_in=sigbody, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.sigbody.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_sigbody(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    signature = create_random_signature(db, faker)
    sigbody = create_random_sigbody(db, faker, signature.id)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.sigbody.remove(db, _id=sigbody.id, audit_logger=audit_logger)

    assert db_obj.id == sigbody.id

    db_obj = crud.sigbody.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_sigbodies_for_signature(db: Session, faker: Faker) -> None:
    signature = create_random_signature(db, faker)
    sigbody = create_random_sigbody(db, faker, signature.id)

    db_obj = crud.sigbody.get_sigbodies_for_signature(db, signature.id)

    assert len(db_obj) == 1
    assert db_obj[0].id == sigbody.id

    db_obj = crud.sigbody.get_sigbodies_for_signature(db, -1)

    assert len(db_obj) == 0
