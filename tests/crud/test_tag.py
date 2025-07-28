import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Tag
from app.schemas.tag import TagCreate, TagUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.tag import create_random_tag
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_tag(db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)
    db_obj = crud.tag.get(db, tag.id)

    assert db_obj.id == tag.id

    db_obj = crud.tag.get(db, -1)

    assert db_obj is None


def test_get_multi_tag(db: Session, faker: Faker) -> None:
    tags = []
    for _ in range(5):
        tags.append(create_random_tag(db, faker))

    db_objs = crud.tag.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == tags[0].id for i in db_objs)

    db_objs = crud.tag.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == tags[1].id for i in db_objs)

    db_objs = crud.tag.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.tag.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_tag(db: Session, faker: Faker) -> None:
    tag = TagCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )
    db_obj = crud.tag.create(db, obj_in=tag)

    assert db_obj.id is not None
    assert db_obj.name == tag.name
    assert db_obj.description == tag.description


def test_update_tag(db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)
    update = TagUpdate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )

    db_obj = crud.tag.update(db, db_obj=tag, obj_in=update)

    assert db_obj.id == tag.id
    assert db_obj.name == update.name
    assert db_obj.description == update.description

    update = {}

    db_obj = crud.tag.update(db, db_obj=tag, obj_in=update)

    assert db_obj.id == tag.id

    update = {
        "test": "test"
    }

    db_obj = crud.tag.update(db, db_obj=tag, obj_in=update)

    assert db_obj.id == tag.id
    assert not hasattr(db_obj, "test")

    update = {
        "name": f"{faker.word().lower()}_{faker.pyint()}",
        "description": faker.sentence(),
    }

    db_obj = crud.tag.update(db, db_obj=Tag(), obj_in=update)

    assert db_obj.id == tag.id + 1
    assert db_obj.name == update["name"]
    assert db_obj.description == update["description"]


def test_remove_tag(db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)

    db_obj = crud.tag.remove(db, _id=tag.id)

    assert db_obj.id == tag.id

    db_obj_del = crud.tag.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.tag.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_tag(db: Session, faker: Faker) -> None:
    tag = TagCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )

    db_obj = crud.tag.get_or_create(db, obj_in=tag)

    assert db_obj.id is not None

    same_db_obj = crud.tag.get_or_create(db, obj_in=tag)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_tag(db: Session, faker: Faker) -> None:
    tags = []
    for _ in range(5):
        tags.append(create_random_tag(db, faker))

    random_tag = random.choice(tags)

    db_obj, count = crud.tag.query_with_filters(db, filter_dict={"id": random_tag.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_tag.id

    db_obj, count = crud.tag.query_with_filters(db, filter_dict={"name": f"!{random_tag.name}"})

    assert db_obj is not None
    assert all(a.name != random_tag.name for a in db_obj)


def test_get_with_roles_tag(db: Session, faker: Faker) -> None:
    tags = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        tag = TagCreate(
            name=f"{faker.word()}_{faker.pyint()}",
            description=faker.sentence(),
        )
        roles.append(role)

        tags.append(crud.tag.create_with_permissions(db, obj_in=tag, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.tag.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_tag(db: Session, faker: Faker) -> None:
    tags = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        tag = TagCreate(
            name=f"{faker.word()}_{faker.pyint()}",
            description=faker.sentence(),
        )
        roles.append(role)

        tags.append(crud.tag.create_with_permissions(db, obj_in=tag, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.tag.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_tag(db: Session, faker: Faker) -> None:
    tag = TagCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.tag.create_with_owner(db, obj_in=tag, owner=owner)

    assert db_obj is not None
    assert db_obj.name == tag.name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_tag(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    tag = TagCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )

    db_obj = crud.tag.create_with_permissions(db, obj_in=tag, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.name == tag.name
    assert db_obj.description == tag.description

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.tag, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_tag(db: Session, faker: Faker) -> None:
    tag = TagCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.tag.create_in_object(db, obj_in=tag, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.name == tag.name

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_tag(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    tag = TagCreate(
        name=f"{faker.word()}_{faker.pyint()}",
        description=faker.sentence(),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.tag.create(db, obj_in=tag, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.tag.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_tag(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    tag = create_random_tag(db, faker, user.username)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.tag.remove(db, _id=tag.id, audit_logger=audit_logger)

    assert db_obj.id == tag.id

    db_obj = crud.tag.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_tag_by_name(db: Session, faker: Faker) -> None:
    tag = create_random_tag(db, faker)
    db_obj = crud.tag.get_by_name(db, tag.name)

    assert db_obj.id == tag.id

    db_obj = crud.tag.get(db, "")

    assert db_obj is None


def test_assign(db: Session, faker: Faker) -> None:
    db_obj = crud.tag.assign(db, -1, TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    tag = create_random_tag(db, faker)

    db_obj = crud.tag.assign(db, tag.id, TargetTypeEnum.alertgroup, -1)

    assert db_obj.id == tag.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": -1, "v1_type": TargetTypeEnum.tag, "v1_id": tag.id})

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].v0_id == -1
    assert db_obj[0].v1_id == tag.id

    tag = create_random_tag(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    crud.tag.assign(db, tag.id, TargetTypeEnum.alertgroup, alertgroup.id)
    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": alertgroup.id, "v1_type": TargetTypeEnum.tag, "v1_id": tag.id})

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].v0_id == alertgroup.id
    assert db_obj[0].v1_id == tag.id


def test_assign_by_name(db: Session, faker: Faker) -> None:
    db_obj = crud.tag.assign_by_name(db, "", TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    tag = create_random_tag(db, faker)

    db_obj = crud.tag.assign_by_name(db, tag.name, TargetTypeEnum.alertgroup, -1)

    assert db_obj.id == tag.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": -1, "v1_type": TargetTypeEnum.tag, "v1_id": tag.id})

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].v0_id == -1
    assert db_obj[0].v1_id == tag.id

    tag = create_random_tag(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    crud.tag.assign_by_name(db, tag.name, TargetTypeEnum.alertgroup, alertgroup.id)
    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": alertgroup.id, "v1_type": TargetTypeEnum.tag, "v1_id": tag.id})

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].v0_id == alertgroup.id
    assert db_obj[0].v1_id == tag.id

    name = f"{faker.word().lower()}_{faker.pyint()}"
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    db_obj = crud.tag.assign_by_name(db, name, TargetTypeEnum.alertgroup, alertgroup.id)

    assert db_obj is None

    db_obj = crud.tag.assign_by_name(db, name, TargetTypeEnum.alertgroup, alertgroup.id, True)

    assert tag.id + 1 == db_obj.id
    assert db_obj.name == name


def test_unassign(db: Session, faker: Faker) -> None:
    db_obj = crud.tag.unassign(db, -1, TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    tag = create_random_tag(db, faker, TargetTypeEnum.alertgroup, alertgroup.id)

    db_obj = crud.tag.unassign(db, tag.id, TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    db_obj = crud.tag.unassign(db, tag.id, TargetTypeEnum.alertgroup, alertgroup.id)

    assert db_obj.id == tag.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": alertgroup.id, "v1_type": TargetTypeEnum.tag, "v1_id": tag.id})

    assert len(db_obj) == 0
    assert count == 0


def test_unassign_by_name(db: Session, faker: Faker) -> None:
    db_obj = crud.tag.unassign_by_name(db, "", TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    tag = create_random_tag(db, faker, TargetTypeEnum.alertgroup, alertgroup.id)

    db_obj = crud.tag.unassign_by_name(db, tag.name, TargetTypeEnum.alertgroup, -1)

    assert db_obj is None

    db_obj = crud.tag.unassign_by_name(db, tag.name, TargetTypeEnum.alertgroup, alertgroup.id)

    assert db_obj.id == tag.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v0_type": TargetTypeEnum.alertgroup, "v0_id": alertgroup.id, "v1_type": TargetTypeEnum.tag, "v1_id": tag.id})

    assert len(db_obj) == 0
    assert count == 0
