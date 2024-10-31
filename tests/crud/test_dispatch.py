import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TlpEnum, StatusEnum, PermissionEnum, TargetTypeEnum
from app.api.deps import AuditLogger
from app.models import Dispatch
from app.schemas.dispatch import DispatchCreate, DispatchUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.dispatch import create_random_dispatch
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_dispatch(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, owner.username, create_extras=False)
    db_obj = crud.dispatch.get(db, dispatch.id)

    assert db_obj.id == dispatch.id

    db_obj = crud.dispatch.get(db, -1)

    assert db_obj is None


def test_get_multi_dispatch(db: Session, faker: Faker) -> None:
    dispatches = []

    owner = create_random_user(db, faker)
    for _ in range(3):
        dispatches.append(create_random_dispatch(db, faker, owner.username, create_extras=False))

    db_objs = crud.dispatch.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == dispatches[0].id for i in db_objs)

    db_objs = crud.dispatch.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == dispatches[1].id for i in db_objs)

    db_objs = crud.dispatch.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.dispatch.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_dispatch(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = DispatchCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )
    db_obj = crud.dispatch.create(db, obj_in=dispatch)

    assert db_obj.id is not None
    assert db_obj.owner == dispatch.owner
    assert db_obj.tlp == dispatch.tlp
    assert db_obj.status == dispatch.status
    assert db_obj.subject == dispatch.subject


def test_update_dispatch(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, owner.username, create_extras=False)
    update = DispatchUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )

    db_obj = crud.dispatch.update(db, db_obj=dispatch, obj_in=update)

    assert db_obj.id == dispatch.id
    assert db_obj.owner == update.owner
    assert db_obj.tlp == update.tlp
    assert db_obj.status == update.status
    assert db_obj.subject == update.subject

    update = {}

    db_obj = crud.dispatch.update(db, db_obj=dispatch, obj_in=update)

    assert db_obj.id == dispatch.id

    update = {
        "test": "test"
    }

    db_obj = crud.dispatch.update(db, db_obj=dispatch, obj_in=update)

    assert db_obj.id == dispatch.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "status": random.choice(list(StatusEnum)),
        "subject": faker.sentence(),
    }

    db_obj = crud.dispatch.update(db, db_obj=Dispatch(), obj_in=update)

    assert db_obj.id == dispatch.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.status == update["status"]
    assert db_obj.subject == update["subject"]


def test_remove_dispatch(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, owner.username, create_extras=False)

    db_obj = crud.dispatch.remove(db, _id=dispatch.id)

    assert db_obj.id == dispatch.id

    db_obj_del = crud.dispatch.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.dispatch.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_dispatch(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = DispatchCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )

    db_obj = crud.dispatch.get_or_create(db, obj_in=dispatch)

    assert db_obj.id is not None

    same_db_obj = crud.dispatch.get_or_create(db, obj_in=dispatch)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_dispatch(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatches = []
    for _ in range(5):
        dispatches.append(create_random_dispatch(db, faker, owner.username, create_extras=False))

    random_dispatch = random.choice(dispatches)

    db_obj, count = crud.dispatch.query_with_filters(db, filter_dict={"id": random_dispatch.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_dispatch.id

    db_obj, count = crud.dispatch.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(dispatches)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.dispatch.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(dispatches) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.dispatch.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.dispatch.query_with_filters(db, filter_dict={"subject": random_dispatch.subject}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.subject == random_dispatch.subject for a in db_obj)

    promoted_obj = crud.promotion.promote(db, [{"type": TargetTypeEnum.dispatch, "id": random_dispatch.id}], TargetTypeEnum.event)
    db_obj, count = crud.dispatch.query_with_filters(db, filter_dict={"promoted_to": f"{TargetTypeEnum.event.value}:{promoted_obj.id}"}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert db_obj[0].promoted_to_targets[0].p0_id == random_dispatch.id
    assert db_obj[0].promoted_to_targets[0].p1_id == promoted_obj.id

    db_obj, count = crud.dispatch.query_with_filters(db, filter_dict={"subject": f"!{random_dispatch.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_dispatch.subject for a in db_obj)


def test_get_with_roles_dispatch(db: Session, faker: Faker) -> None:
    dispatches = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        dispatch = DispatchCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
        )
        roles.append(role)

        dispatches.append(crud.dispatch.create_with_permissions(db, obj_in=dispatch, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.dispatch.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_dispatch(db: Session, faker: Faker) -> None:
    dispatches = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        dispatch = DispatchCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
        )
        roles.append(role)

        dispatches.append(crud.dispatch.create_with_permissions(db, obj_in=dispatch, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.dispatch.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_dispatch(db: Session, faker: Faker) -> None:
    dispatch = DispatchCreate(
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.dispatch.create_with_owner(db, obj_in=dispatch, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == dispatch.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_dispatch(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    dispatch = DispatchCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )

    db_obj = crud.dispatch.create_with_permissions(db, obj_in=dispatch, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == dispatch.owner
    assert db_obj.tlp == dispatch.tlp
    assert db_obj.status == dispatch.status
    assert db_obj.subject == dispatch.subject

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.dispatch, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_dispatch(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = DispatchCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.dispatch.create_in_object(db, obj_in=dispatch, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == dispatch.subject

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_dispatch(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    dispatch = DispatchCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.dispatch.create(db, obj_in=dispatch, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.dispatch.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_dispatch(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    dispatch = create_random_dispatch(db, faker, user.username, create_extras=False)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.dispatch.remove(db, _id=dispatch.id, audit_logger=audit_logger)

    assert db_obj.id == dispatch.id

    db_obj = crud.dispatch.undelete(db, db_obj.id)

    assert db_obj is None
