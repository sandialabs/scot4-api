import random
import pytest
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Pivot
from app.schemas.pivot import PivotCreate, PivotUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.pivot import create_random_pivot
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user
from tests.utils.entity_type import create_random_entity_type
from tests.utils.entity_class import create_random_entity_class


def test_get_pivot(db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)
    db_obj = crud.pivot.get(db, pivot.id)

    assert db_obj.id == pivot.id

    db_obj = crud.pivot.get(db, -1)

    assert db_obj is None


def test_get_multi_pivot(db: Session, faker: Faker) -> None:
    pivots = []
    for _ in range(5):
        pivots.append(create_random_pivot(db, faker))

    db_objs = crud.pivot.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == pivots[0].id for i in db_objs)

    db_objs = crud.pivot.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == pivots[1].id for i in db_objs)

    db_objs = crud.pivot.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.pivot.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_pivot(db: Session, faker: Faker) -> None:
    pivot = PivotCreate(
        title=faker.sentence(),
        template=faker.sentence(),
        description=faker.sentence()
    )
    db_obj = crud.pivot.create(db, obj_in=pivot)

    assert db_obj.id is not None
    assert db_obj.title == pivot.title
    assert db_obj.template == pivot.template
    assert db_obj.description == pivot.description


def test_update_pivot(db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)
    update = PivotUpdate(
        title=faker.sentence(),
        template=faker.sentence(),
        description=faker.sentence()
    )

    db_obj = crud.pivot.update(db, db_obj=pivot, obj_in=update)

    assert db_obj.id == pivot.id
    assert db_obj.title == update.title
    assert db_obj.template == update.template
    assert db_obj.description == update.description

    update = {}

    db_obj = crud.pivot.update(db, db_obj=pivot, obj_in=update)

    assert db_obj.id == pivot.id

    update = {
        "test": "test"
    }

    db_obj = crud.pivot.update(db, db_obj=pivot, obj_in=update)

    assert db_obj.id == pivot.id
    assert not hasattr(db_obj, "test")

    update = {
        "title": faker.sentence(),
        "template": faker.sentence(),
        "description": faker.sentence()
    }

    db_obj = crud.pivot.update(db, db_obj=Pivot(), obj_in=update)

    assert db_obj.id == pivot.id + 1
    assert db_obj.title == update["title"]
    assert db_obj.template == update["template"]
    assert db_obj.description == update["description"]


def test_remove_pivot(db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)

    db_obj = crud.pivot.remove(db, _id=pivot.id)

    assert db_obj.id == pivot.id

    db_obj_del = crud.pivot.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.pivot.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_pivot(db: Session, faker: Faker) -> None:
    pivot = PivotCreate(
        title=faker.sentence(),
        template=faker.sentence(),
        description=faker.sentence()
    )

    db_obj = crud.pivot.get_or_create(db, obj_in=pivot)

    assert db_obj.id is not None

    same_db_obj = crud.pivot.get_or_create(db, obj_in=pivot)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_pivot(db: Session, faker: Faker) -> None:
    pivots = []
    for _ in range(5):
        pivots.append(create_random_pivot(db, faker))

    random_pivot = random.choice(pivots)

    db_obj, count = crud.pivot.query_with_filters(db, filter_dict={"id": random_pivot.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_pivot.id

    db_obj, count = crud.pivot.query_with_filters(db, filter_dict={"description": f"!{random_pivot.description}"})

    assert db_obj is not None
    assert all(a.description != random_pivot.description for a in db_obj)


def test_get_with_roles_pivot(db: Session, faker: Faker) -> None:
    pivots = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        pivot = PivotCreate(
            title=faker.sentence(),
            template=faker.sentence(),
            description=faker.sentence()
        )
        roles.append(role)

        pivots.append(crud.pivot.create_with_permissions(db, obj_in=pivot, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.pivot.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_pivot(db: Session, faker: Faker) -> None:
    pivots = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        pivot = PivotCreate(
            title=faker.sentence(),
            template=faker.sentence(),
            description=faker.sentence()
        )
        roles.append(role)

        pivots.append(crud.pivot.create_with_permissions(db, obj_in=pivot, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.pivot.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_pivot(db: Session, faker: Faker) -> None:
    pivot = PivotCreate(
        title=faker.sentence(),
        template=faker.sentence(),
        description=faker.sentence()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.pivot.create_with_owner(db, obj_in=pivot, owner=owner)

    assert db_obj is not None
    assert db_obj.title == pivot.title
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_pivot(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    pivot = PivotCreate(
        title=faker.sentence(),
        template=faker.sentence(),
        description=faker.sentence()
    )

    db_obj = crud.pivot.create_with_permissions(db, obj_in=pivot, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.title == pivot.title
    assert db_obj.template == pivot.template
    assert db_obj.description == pivot.description

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.pivot, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_pivot(db: Session, faker: Faker) -> None:
    pivot = PivotCreate(
        title=faker.sentence(),
        template=faker.sentence(),
        description=faker.sentence()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.pivot.create_in_object(db, obj_in=pivot, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.title == pivot.title

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count >= 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_pivot(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    pivot = PivotCreate(
        title=faker.sentence(),
        template=faker.sentence(),
        description=faker.sentence()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.pivot.create(db, obj_in=pivot, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.pivot.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_pivot(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    pivot = create_random_pivot(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.pivot.remove(db, _id=pivot.id, audit_logger=audit_logger)

    assert db_obj.id == pivot.id

    db_obj = crud.pivot.undelete(db, db_obj.id)

    assert db_obj is None


def test_add_entity_classes(db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)
    entity_class = create_random_entity_class(db, faker)

    db_obj = crud.pivot.add_entity_classes(db, pivot, [entity_class.id])

    assert db_obj is not None
    assert db_obj.id == pivot.id
    assert len(db_obj.entity_classes) == 1
    assert db_obj.linked_entity_class_count == 1
    assert db_obj.entity_classes[0].id == entity_class.id

    pivot = create_random_pivot(db, faker)
    entity_class = create_random_entity_class(db, faker)

    db_obj = crud.pivot.add_entity_classes(db, pivot, [entity_class.name])

    assert db_obj is not None
    assert db_obj.id == pivot.id
    assert len(db_obj.entity_classes) == 1
    assert db_obj.linked_entity_class_count == 1
    assert db_obj.entity_classes[0].id == entity_class.id

    with pytest.raises(Exception):
        db_obj = crud.pivot.add_entity_classes(db, pivot, [-1])


def test_add_entity_types(db: Session, faker: Faker) -> None:
    pivot = create_random_pivot(db, faker)
    entity_type = create_random_entity_type(db, faker)

    db_obj = crud.pivot.add_entity_types(db, pivot, [entity_type.id])

    assert db_obj is not None
    assert db_obj.id == pivot.id
    assert len(db_obj.entity_types) == 1
    assert db_obj.linked_entity_type_count == 1
    assert db_obj.entity_types[0].id == entity_type.id

    pivot = create_random_pivot(db, faker)
    entity_type = create_random_entity_type(db, faker)

    db_obj = crud.pivot.add_entity_types(db, pivot, [entity_type.name])

    assert db_obj is not None
    assert db_obj.id == pivot.id
    assert len(db_obj.entity_types) == 1
    assert db_obj.linked_entity_type_count == 1
    assert db_obj.entity_types[0].id == entity_type.id

    with pytest.raises(Exception):
        db_obj = crud.pivot.add_entity_types(db, pivot, [-1])
