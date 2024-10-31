import random
import json
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum, EntryClassEnum
from app.models import Entry
from app.schemas.alertgroup import AlertGroupCreate
from app.schemas.entry import EntryCreate, EntryUpdate

from tests.utils.entity import create_random_entity
from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.entry import create_random_entry
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


TARGET_LIST = list(TargetTypeEnum)
TARGET_LIST.remove(TargetTypeEnum.none)
TARGET_LIST.remove(TargetTypeEnum.remote_flair)


def test_get_entry(db: Session, faker: Faker) -> None:
    entry = create_random_entry(db, faker)
    db_obj = crud.entry.get(db, entry.id)

    assert db_obj.id == entry.id

    db_obj = crud.entry.get(db, -1)

    assert db_obj is None


def test_get_multi_entry(db: Session, faker: Faker) -> None:
    entries = []
    for _ in range(3):
        entries.append(create_random_entry(db, faker))

    db_objs = crud.entry.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == entries[0].id for i in db_objs)

    db_objs = crud.entry.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == entries[1].id for i in db_objs)

    db_objs = crud.entry.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.entry.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_entry(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entry = EntryCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        target_type=random.choice(TARGET_LIST),
        target_id=faker.pyint(),
        entry_class=random.choice(list(EntryClassEnum))
    )
    db_obj = crud.entry.create(db, obj_in=entry)

    assert db_obj.id is not None
    assert db_obj.owner == entry.owner
    assert db_obj.tlp == entry.tlp
    assert db_obj.target_type == entry.target_type
    assert db_obj.target_id == entry.target_id
    assert db_obj.entry_class == entry.entry_class


def test_update_entry(db: Session, faker: Faker) -> None:
    entry = create_random_entry(db, faker)
    owner = create_random_user(db, faker)
    update = EntryUpdate(
        owner=owner.username,
        target_type=random.choice(TARGET_LIST),
        target_id=faker.pyint(),
        parsed=faker.pybool()
    )

    db_obj = crud.entry.update(db, db_obj=entry, obj_in=update)

    assert db_obj.id == entry.id
    assert db_obj.owner == update.owner
    assert db_obj.target_type == update.target_type

    update = {}

    db_obj = crud.entry.update(db, db_obj=entry, obj_in=update)

    assert db_obj.id == entry.id

    update = {
        "test": "test"
    }

    db_obj = crud.entry.update(db, db_obj=entry, obj_in=update)

    assert db_obj.id == entry.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "target_type": random.choice(TARGET_LIST),
        "target_id": faker.pyint(),
        "parsed": faker.pybool()
    }

    db_obj = crud.entry.update(db, db_obj=Entry(), obj_in=update)

    assert db_obj.id == entry.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.target_type == update["target_type"]
    assert db_obj.target_id == update["target_id"]
    assert db_obj.parsed == update["parsed"]

    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    # need to track this separately otherwise the tests will fail
    ag_modified = alertgroup.modified
    entry = create_random_entry(db, faker, alertgroup.owner, target_type=TargetTypeEnum.alertgroup, target_id=alertgroup.id)
    update = {
        "tlp": random.choice(list(TlpEnum))
    }
    db_obj = crud.entry.update(db, db_obj=entry, obj_in=update)

    alertgroup_obj = crud.alert_group.get(db, alertgroup.id)
    assert ag_modified != alertgroup_obj.modified


def test_remove_entry(db: Session, faker: Faker) -> None:
    entry = create_random_entry(db, faker)

    db_obj = crud.entry.remove(db, _id=entry.id)

    assert db_obj.id == entry.id

    db_obj_del = crud.entry.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.entry.remove(db, _id=-1)

    assert db_obj is None

    grand_parent_entry = create_random_entry(db, faker)
    parent_entry = create_random_entry(db, faker, grand_parent_entry.owner, grand_parent_entry.id)
    entry = create_random_entry(db, faker, parent_entry.owner, parent_entry.id)

    db_obj = crud.entry.remove(db, _id=parent_entry.id)

    db_obj = crud.entry.get(db, grand_parent_entry.id)

    assert len(db_obj.child_entries) == 1
    assert db_obj.child_entries[0].id == entry.id


def test_get_or_create_entry(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entry = EntryCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        target_type=random.choice(TARGET_LIST),
        target_id=faker.pyint(),
        entry_class=random.choice(list(EntryClassEnum))
    )

    db_obj = crud.entry.get_or_create(db, obj_in=entry)

    assert db_obj.id is not None

    same_db_obj = crud.entry.get_or_create(db, obj_in=entry)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_entry(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, owner.username, with_alerts=False)
    parent_entry = create_random_entry(db, faker, target_id=alertgroup.id, target_type=TargetTypeEnum.alertgroup)
    entries = []
    assignees = []
    statues = []
    for _ in range(3):
        assign = f"{faker.word()}_{faker.pyint()}"
        assignees.append(assign)
        status = f"{faker.word()}_{faker.pyint()}"
        statues.append(status)
        entries.append(create_random_entry(db, faker, owner.username, parent_entry_id=parent_entry.id, assignee=assign, status=status))

    random_entry = random.choice(entries)

    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"id": random_entry.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_entry.id

    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(entries)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(entries) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert count == len(entries)
    assert all(a.owner == owner.username for a in db_obj)

    random_assignee = random.choice(assignees)
    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"task_assignee": random_assignee})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].entry_data["assignee"] == random_assignee

    random_status = random.choice(statues)
    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"task_status": random_status})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].entry_data["status"] == random_status

    random_assignee = random.choice(assignees)
    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"task_assignee": f"!{random_assignee}"})

    assert db_obj is not None
    assert all(random_assignee not in json.dumps(a.entry_data) for a in db_obj)

    random_assignee = random.choice(assignees)
    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"task_assignee": f"!{random_assignee}"})

    assert db_obj is not None
    assert all(random_assignee not in json.dumps(a.entry_data) for a in db_obj)

    random_status = random.choice(statues)
    db_obj, count = crud.entry.query_with_filters(db, filter_dict={"task_status": f"!{random_status}"})

    assert db_obj is not None
    assert all(random_status not in json.dumps(a.entry_data) for a in db_obj)


def test_get_with_roles_entry(db: Session, faker: Faker) -> None:
    entries = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        # create a target
        alertgroup = AlertGroupCreate(
            owner=owner.username,
            subject=faker.sentence()
        )
        alertgroup = crud.alert_group.create_with_permissions(db, obj_in=alertgroup, perm_in={PermissionEnum.read: [role.id]})

        entry = EntryCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            target_type=TargetTypeEnum.alertgroup,
            target_id=alertgroup.id,
            entry_class=random.choice(list(EntryClassEnum))
        )
        roles.append(role)
        entries.append(crud.entry.create_with_permissions(db, obj_in=entry, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.entry.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_entry(db: Session, faker: Faker) -> None:
    entries = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        # create a target
        alertgroup = AlertGroupCreate(
            owner=owner.username,
            subject=faker.sentence()
        )
        alertgroup = crud.alert_group.create_with_permissions(db, obj_in=alertgroup, perm_in={PermissionEnum.read: [role.id]})

        entry = EntryCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            target_type=TargetTypeEnum.alertgroup,
            target_id=alertgroup.id,
            entry_class=random.choice(list(EntryClassEnum))
        )
        roles.append(role)

        entries.append(crud.entry.create_with_permissions(db, obj_in=entry, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.entry.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_entry(db: Session, faker: Faker) -> None:
    entry = EntryCreate(
        tlp=random.choice(list(TlpEnum)),
        target_type=random.choice(TARGET_LIST),
        target_id=faker.pyint(),
        entry_class=random.choice(list(EntryClassEnum))
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.entry.create_with_owner(db, obj_in=entry, owner=owner)

    assert db_obj is not None
    assert db_obj.tlp == entry.tlp
    assert db_obj.target_type == entry.target_type
    assert db_obj.target_id == entry.target_id
    assert db_obj.entry_class == entry.entry_class
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_entry(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    entry = EntryCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        target_type=random.choice(TARGET_LIST),
        target_id=faker.pyint(),
        entry_class=random.choice(list(EntryClassEnum))
    )

    db_obj = crud.entry.create_with_permissions(db, obj_in=entry, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == entry.owner
    assert db_obj.tlp == entry.tlp
    assert db_obj.target_type == entry.target_type
    assert db_obj.target_id == entry.target_id
    assert db_obj.entry_class == entry.entry_class

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.entry, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_entry(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entry = EntryCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        target_type=random.choice(TARGET_LIST),
        target_id=faker.pyint(),
        entry_class=random.choice(list(EntryClassEnum))
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.entry.create_in_object(db, obj_in=entry, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.owner == entry.owner

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_entry(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entry = EntryCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        target_type=random.choice(TARGET_LIST),
        target_id=faker.pyint(),
        entry_class=random.choice(list(EntryClassEnum))
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.entry.create(db, obj_in=entry, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.entry.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_entry(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entry = create_random_entry(db, faker, user.username)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.entry.remove(db, _id=entry.id, audit_logger=audit_logger)

    assert db_obj.id == entry.id

    db_obj = crud.entry.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_by_type_entry(db: Session, faker: Faker) -> None:
    entries = []
    alertgroup = create_random_alertgroup_no_sig(db, faker)
    for _ in range(3):
        entries.append(create_random_entry(db, faker, target_type=TargetTypeEnum.alertgroup, target_id=alertgroup.id))

    db_obj, count = crud.entry.get_by_type(db, _id=alertgroup.id, _type=TargetTypeEnum.alertgroup)

    assert len(db_obj) == len(entries)
    assert count == len(entries)
    assert all(i.target_id == alertgroup.id for i in db_obj)

    db_obj, count = crud.entry.get_by_type(db, _id=alertgroup.id, _type=TargetTypeEnum.alertgroup, skip=1)

    assert len(db_obj) == len(entries) - 1
    assert count == len(entries)

    db_obj, count = crud.entry.get_by_type(db, _id=alertgroup.id, _type=TargetTypeEnum.alertgroup, limit=1)

    assert len(db_obj) == 1
    assert count == len(entries)

    db_obj, count = crud.entry.get_by_type(db, _id=alertgroup.id, _type=TargetTypeEnum.alertgroup, skip=1, limit=1)

    assert len(db_obj) == 1
    assert count == len(entries)
    assert entries[1].id == db_obj[0].id


def test_flair_update_entry(db: Session, faker: Faker) -> None:
    entry = create_random_entry(db, faker)
    entity = create_random_entity(db, faker, enrich=False, pivot=False)
    text_flaired = faker.sentence()
    text = faker.sentence()
    text_plain = faker.sentence()

    db_obj = crud.entry.flair_update(db, entry.id, text_flaired, {entity.entity_type.name: [entity.value]}, text, text_plain)

    assert db_obj.id == entry.id
    assert db_obj.entry_data["html"] == text
    assert db_obj.entry_data["plain_text"] == text_plain
    assert db_obj.entry_data["flaired_html"] == text_flaired
    assert db_obj.entry_data["flaired"] is True
