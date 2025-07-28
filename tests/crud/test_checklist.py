import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum
from app.models import Checklist
from app.schemas.checklist import ChecklistCreate, ChecklistUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.checklist import create_random_checklist
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_checklist(db: Session, faker: Faker) -> None:
    checklist = create_random_checklist(db, faker)
    db_obj = crud.checklist.get(db, checklist.id)

    assert db_obj.id == checklist.id

    db_obj = crud.checklist.get(db, -1)

    assert db_obj is None


def test_get_multi_checklist(db: Session, faker: Faker) -> None:
    checklists = []
    for _ in range(5):
        checklists.append(create_random_checklist(db, faker))

    db_objs = crud.checklist.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == checklists[0].id for i in db_objs)

    db_objs = crud.checklist.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == checklists[1].id for i in db_objs)

    db_objs = crud.checklist.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.checklist.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_checklist(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    checklist = ChecklistCreate(
        owner=owner.username,
        subject=faker.sentence(),
        checklist_data_ver=str(faker.pyfloat(1, 1, True))
    )
    db_obj = crud.checklist.create(db, obj_in=checklist)

    assert db_obj.id is not None
    assert db_obj.owner == checklist.owner
    assert db_obj.subject == checklist.subject
    assert db_obj.checklist_data_ver == checklist.checklist_data_ver


def test_update_checklist(db: Session, faker: Faker) -> None:
    checklist = create_random_checklist(db, faker)
    owner = create_random_user(db, faker)
    update = ChecklistUpdate(
        owner=owner.username,
        subject=faker.sentence(),
        checklist_data_ver=str(faker.pyfloat(1, 1, True))
    )

    db_obj = crud.checklist.update(db, db_obj=checklist, obj_in=update)

    assert db_obj.id == checklist.id
    assert db_obj.owner == update.owner
    assert db_obj.subject == update.subject

    update = {}

    db_obj = crud.checklist.update(db, db_obj=checklist, obj_in=update)

    assert db_obj.id == checklist.id

    update = {
        "test": "test"
    }

    db_obj = crud.checklist.update(db, db_obj=checklist, obj_in=update)

    assert db_obj.id == checklist.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "subject": faker.sentence(),
        "checklist_data_ver": "1.0.0",
        "tlp": random.choice(list(TlpEnum))
    }

    db_obj = crud.checklist.update(db, db_obj=Checklist(), obj_in=update)

    assert db_obj.id == checklist.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.subject == update["subject"]
    assert db_obj.checklist_data_ver == update["checklist_data_ver"]


def test_remove_checklist(db: Session, faker: Faker) -> None:
    checklist = create_random_checklist(db, faker)

    db_obj = crud.checklist.remove(db, _id=checklist.id)

    assert db_obj.id == checklist.id

    db_obj_del = crud.checklist.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.checklist.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_checklist(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    checklist = ChecklistCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence(),
        checklist_data_ver=str(faker.pyfloat(1, 1, True))
    )

    db_obj = crud.checklist.get_or_create(db, obj_in=checklist)

    assert db_obj.id is not None

    same_db_obj = crud.checklist.get_or_create(db, obj_in=checklist)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_checklist(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    checklists = []
    for _ in range(5):
        checklists.append(create_random_checklist(db, faker, owner))

    random_checklist = random.choice(checklists)

    db_obj, count = crud.checklist.query_with_filters(db, filter_dict={"id": random_checklist.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_checklist.id

    db_obj, count = crud.checklist.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(checklists)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.checklist.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(checklists) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.checklist.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.checklist.query_with_filters(db, filter_dict={"subject": f"!{random_checklist.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_checklist.subject for a in db_obj)


def test_get_with_roles_checklist(db: Session, faker: Faker) -> None:
    checklists = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        checklist = ChecklistCreate(
            owner=owner.username,
            subject=faker.sentence(),
            checklist_data_ver=str(faker.pyfloat(1, 1, True))
        )
        roles.append(role)

        checklists.append(crud.checklist.create_with_permissions(db, obj_in=checklist, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.checklist.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_checklist(db: Session, faker: Faker) -> None:
    checklists = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        checklist = ChecklistCreate(
            owner=owner.username,
            subject=faker.sentence(),
            checklist_data_ver=str(faker.pyfloat(1, 1, True))
        )
        roles.append(role)

        checklists.append(crud.checklist.create_with_permissions(db, obj_in=checklist, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.checklist.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_checklist(db: Session, faker: Faker) -> None:
    checklist = ChecklistCreate(
        subject=faker.sentence(),
        checklist_data_ver=str(faker.pyfloat(1, 1, True))
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.checklist.create_with_owner(db, obj_in=checklist, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == checklist.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_checklist(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    checklist = ChecklistCreate(
        owner=owner.username,
        subject=faker.sentence(),
        checklist_data_ver=str(faker.pyfloat(1, 1, True))
    )

    db_obj = crud.checklist.create_with_permissions(db, obj_in=checklist, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == checklist.owner
    assert db_obj.subject == checklist.subject
    assert db_obj.checklist_data_ver == checklist.checklist_data_ver

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.checklist, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_checklist(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    checklist = ChecklistCreate(
        owner=owner.username,
        subject=faker.sentence(),
        checklist_data_ver=str(faker.pyfloat(1, 1, True))
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.checklist.create_in_object(db, obj_in=checklist, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == checklist.subject

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_checklist(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    checklist = ChecklistCreate(
        owner=owner.username,
        subject=faker.sentence(),
        checklist_data_ver=str(faker.pyfloat(1, 1, True))
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.checklist.create(db, obj_in=checklist, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.checklist.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_checklist(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    checklist = create_random_checklist(db, faker, user)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.checklist.remove(db, _id=checklist.id, audit_logger=audit_logger)

    assert db_obj.id == checklist.id

    db_obj = crud.checklist.undelete(db, db_obj.id)

    assert db_obj is None
