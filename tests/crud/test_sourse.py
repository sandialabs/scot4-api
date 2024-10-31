import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Source
from app.schemas.source import SourceCreate, SourceUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.source import create_random_source
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_source(db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)
    db_obj = crud.source.get(db, source.id)

    assert db_obj.id == source.id

    db_obj = crud.source.get(db, -1)

    assert db_obj is None


def test_get_multi_source(db: Session, faker: Faker) -> None:
    sources = []
    for _ in range(5):
        sources.append(create_random_source(db, faker))

    db_objs = crud.source.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == sources[0].id for i in db_objs)

    db_objs = crud.source.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == sources[1].id for i in db_objs)

    db_objs = crud.source.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.source.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_source(db: Session, faker: Faker) -> None:
    source = SourceCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )
    db_obj = crud.source.create(db, obj_in=source)

    assert db_obj.id is not None
    assert db_obj.name == source.name
    assert db_obj.description == source.description


def test_update_source(db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)
    update = SourceUpdate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )

    db_obj = crud.source.update(db, db_obj=source, obj_in=update)

    assert db_obj.id == source.id
    assert db_obj.name == update.name
    assert db_obj.description == update.description

    update = {}

    db_obj = crud.source.update(db, db_obj=source, obj_in=update)

    assert db_obj.id == source.id

    update = {
        "test": "test"
    }

    db_obj = crud.source.update(db, db_obj=source, obj_in=update)

    assert db_obj.id == source.id
    assert not hasattr(db_obj, "test")

    update = {
        "name": f"{faker.word()}_{faker.pyint()}",
        "description": faker.sentence(),
    }

    db_obj = crud.source.update(db, db_obj=Source(), obj_in=update)

    assert db_obj.id == source.id + 1
    assert db_obj.name == update["name"]
    assert db_obj.description == update["description"]


def test_remove_source(db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)

    db_obj = crud.source.remove(db, _id=source.id)

    assert db_obj.id == source.id

    db_obj_del = crud.source.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.source.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_source(db: Session, faker: Faker) -> None:
    source = SourceCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )

    db_obj = crud.source.get_or_create(db, obj_in=source)

    assert db_obj.id is not None

    same_db_obj = crud.source.get_or_create(db, obj_in=source)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_source(db: Session, faker: Faker) -> None:
    sources = []
    for _ in range(5):
        sources.append(create_random_source(db, faker))

    random_source = random.choice(sources)

    db_obj, count = crud.source.query_with_filters(db, filter_dict={"id": random_source.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_source.id

    db_obj, count = crud.source.query_with_filters(db, filter_dict={"name": f"!{random_source.name}"})

    assert db_obj is not None
    assert all(a.name != random_source.name for a in db_obj)


def test_get_with_roles_source(db: Session, faker: Faker) -> None:
    sources = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        source = SourceCreate(
            name=f"{faker.word()}_{faker.pyint()}",
            description=faker.sentence(),
        )
        roles.append(role)

        sources.append(crud.source.create_with_permissions(db, obj_in=source, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.source.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_source(db: Session, faker: Faker) -> None:
    sources = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        source = SourceCreate(
            name=f"{faker.word()}_{faker.pyint()}",
            description=faker.sentence(),
        )
        roles.append(role)

        sources.append(crud.source.create_with_permissions(db, obj_in=source, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.source.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_source(db: Session, faker: Faker) -> None:
    source = SourceCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.source.create_with_owner(db, obj_in=source, owner=owner)

    assert db_obj is not None
    assert db_obj.name == source.name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_source(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    source = SourceCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )

    db_obj = crud.source.create_with_permissions(db, obj_in=source, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.name == source.name
    assert db_obj.description == source.description

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.source, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_source(db: Session, faker: Faker) -> None:
    source = SourceCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.source.create_in_object(db, obj_in=source, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.name == source.name

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v0_target": TargetTypeEnum.alertgroup, "v1_id": db_obj.id, "v1_target": TargetTypeEnum.source})

    assert count >= 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_source(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    source = SourceCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.source.create(db, obj_in=source, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.source.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_source(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    source = create_random_source(db, faker, user.username)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.source.remove(db, _id=source.id, audit_logger=audit_logger)

    assert db_obj.id == source.id

    db_obj = crud.source.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_source_by_name(db: Session, faker: Faker) -> None:
    source = create_random_source(db, faker)
    db_obj = crud.source.get_by_name(db, source.name)

    assert db_obj.id == source.id

    db_obj = crud.source.get(db, "")

    assert db_obj is None


def test_assign(db: Session, faker: Faker) -> None:
    db_obj = crud.source.assign(db, -1, TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    source = create_random_source(db, faker)

    db_obj = crud.source.assign(db, source.id, TargetTypeEnum.alertgroup, -1)

    assert db_obj.id == source.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": -1, "v1_type": TargetTypeEnum.source, "v1_id": source.id})

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].v0_id == -1
    assert db_obj[0].v1_id == source.id

    source = create_random_source(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    crud.source.assign(db, source.id, TargetTypeEnum.alertgroup, alertgroup.id)
    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": alertgroup.id, "v1_type": TargetTypeEnum.source, "v1_id": source.id})

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].v0_id == alertgroup.id
    assert db_obj[0].v1_id == source.id


def test_assign_by_name(db: Session, faker: Faker) -> None:
    db_obj = crud.source.assign_by_name(db, "", TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    source = create_random_source(db, faker)

    db_obj = crud.source.assign_by_name(db, source.name, TargetTypeEnum.alertgroup, -1)

    assert db_obj.id == source.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": -1, "v1_type": TargetTypeEnum.source, "v1_id": source.id})

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].v0_id == -1
    assert db_obj[0].v1_id == source.id

    source = create_random_source(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    crud.source.assign_by_name(db, source.name, TargetTypeEnum.alertgroup, alertgroup.id)
    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": alertgroup.id, "v1_type": TargetTypeEnum.source, "v1_id": source.id})

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].v0_id == alertgroup.id
    assert db_obj[0].v1_id == source.id

    name = f"{faker.word().lower()}_{faker.pyint()}"
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    db_obj = crud.source.assign_by_name(db, name, TargetTypeEnum.alertgroup, alertgroup.id)

    assert db_obj is None

    db_obj = crud.source.assign_by_name(db, name, TargetTypeEnum.alertgroup, alertgroup.id, True)

    assert source.id + 1 == db_obj.id
    assert db_obj.name == name


def test_unassign(db: Session, faker: Faker) -> None:
    db_obj = crud.source.unassign(db, -1, TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    source = create_random_source(db, faker, TargetTypeEnum.alertgroup, alertgroup.id)

    db_obj = crud.source.unassign(db, source.id, TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    db_obj = crud.source.unassign(db, source.id, TargetTypeEnum.alertgroup, alertgroup.id)

    assert db_obj.id == source.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": alertgroup.id, "v1_type": TargetTypeEnum.source, "v1_id": source.id})

    assert len(db_obj) == 0
    assert count == 0


def test_unassign_by_name(db: Session, faker: Faker) -> None:
    db_obj = crud.source.unassign_by_name(db, "", TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    source = create_random_source(db, faker, TargetTypeEnum.alertgroup, alertgroup.id)

    db_obj = crud.source.unassign_by_name(db, source.name, TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    db_obj = crud.source.unassign_by_name(db, source.name, TargetTypeEnum.alertgroup, alertgroup.id)

    assert db_obj.id == source.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": alertgroup.id, "v1_type": TargetTypeEnum.source, "v1_id": source.id})

    assert len(db_obj) == 0
    assert count == 0