import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum, StatusEnum
from app.models import Intel
from app.schemas.intel import IntelCreate, IntelUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.intel import create_random_intel
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role
from tests.utils.event import create_random_event


def test_get_intel(db: Session, faker: Faker) -> None:
    intel = create_random_intel(db, faker, create_extras=False)
    db_obj = crud.intel.get(db, intel.id)

    assert db_obj.id == intel.id

    db_obj = crud.intel.get(db, -1)

    assert db_obj is None


def test_get_multi_intel(db: Session, faker: Faker) -> None:
    intels = []
    for _ in range(3):
        intels.append(create_random_intel(db, faker, create_extras=False))

    db_objs = crud.intel.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == intels[0].id for i in db_objs)

    db_objs = crud.intel.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == intels[1].id for i in db_objs)

    db_objs = crud.intel.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.intel.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_intel(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = IntelCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )
    db_obj = crud.intel.create(db, obj_in=intel)

    assert db_obj.id is not None
    assert db_obj.owner == intel.owner
    assert db_obj.tlp == intel.tlp
    assert db_obj.status == intel.status
    assert db_obj.subject == intel.subject


def test_update_intel(db: Session, faker: Faker) -> None:
    intel = create_random_intel(db, faker, create_extras=False)
    owner = create_random_user(db, faker)
    update = IntelUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )

    db_obj = crud.intel.update(db, db_obj=intel, obj_in=update)

    assert db_obj.id == intel.id
    assert db_obj.owner == update.owner
    assert db_obj.tlp == update.tlp
    assert db_obj.status == update.status
    assert db_obj.subject == update.subject

    update = {}

    db_obj = crud.intel.update(db, db_obj=intel, obj_in=update)

    assert db_obj.id == intel.id

    update = {
        "test": "test"
    }

    db_obj = crud.intel.update(db, db_obj=intel, obj_in=update)

    assert db_obj.id == intel.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "status": random.choice(list(StatusEnum)),
        "subject": faker.sentence(),
    }

    db_obj = crud.intel.update(db, db_obj=Intel(), obj_in=update)

    assert db_obj.id == intel.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.status == update["status"]
    assert db_obj.subject == update["subject"]


def test_remove_intel(db: Session, faker: Faker) -> None:
    intel = create_random_intel(db, faker, create_extras=False)

    db_obj = crud.intel.remove(db, _id=intel.id)

    assert db_obj.id == intel.id

    db_obj_del = crud.intel.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.intel.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_intel(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = IntelCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )

    db_obj = crud.intel.get_or_create(db, obj_in=intel)

    assert db_obj.id is not None

    same_db_obj = crud.intel.get_or_create(db, obj_in=intel)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_intel(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intels = []
    for _ in range(3):
        intels.append(create_random_intel(db, faker, owner.username, create_extras=False))

    random_intel = random.choice(intels)

    db_obj, count = crud.intel.query_with_filters(db, filter_dict={"id": random_intel.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_intel.id

    db_obj, count = crud.intel.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(intels)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.intel.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(intels) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.intel.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.intel.query_with_filters(db, filter_dict={"subject": random_intel.subject}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0].id == random_intel.id

    event = create_random_event(db, faker)
    promote = crud.promotion.promote(db, [{"type": TargetTypeEnum.event, "id": event.id}], TargetTypeEnum.intel)

    db_obj, count = crud.event.query_with_filters(db, filter_dict={"promoted_to": f"{TargetTypeEnum.intel.value}:{promote.id}"})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == event.id

    db_obj, count = crud.checklist.query_with_filters(db, filter_dict={"subject": f"!{random_intel.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_intel.subject for a in db_obj)


def test_get_with_roles_intel(db: Session, faker: Faker) -> None:
    intels = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        intel = IntelCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
        )
        roles.append(role)

        intels.append(crud.intel.create_with_permissions(db, obj_in=intel, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.intel.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_intel(db: Session, faker: Faker) -> None:
    intels = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        intel = IntelCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
        )
        roles.append(role)

        intels.append(crud.intel.create_with_permissions(db, obj_in=intel, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.intel.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_intel(db: Session, faker: Faker) -> None:
    intel = IntelCreate(
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.intel.create_with_owner(db, obj_in=intel, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == intel.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_intel(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    intel = IntelCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )

    db_obj = crud.intel.create_with_permissions(db, obj_in=intel, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == intel.owner
    assert db_obj.tlp == intel.tlp
    assert db_obj.status == intel.status
    assert db_obj.subject == intel.subject

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.intel, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_intel(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = IntelCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.intel.create_in_object(db, obj_in=intel, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == intel.subject

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_intel(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    intel = IntelCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.intel.create(db, obj_in=intel, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.intel.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_intel(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    intel = create_random_intel(db, faker, user.username, create_extras=False)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.intel.remove(db, _id=intel.id, audit_logger=audit_logger)

    assert db_obj.id == intel.id

    db_obj = crud.intel.undelete(db, db_obj.id)

    assert db_obj is None
