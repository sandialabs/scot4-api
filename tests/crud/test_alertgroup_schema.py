import pytest
import random
from pydantic import ValidationError
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import AlertGroupSchemaKeys
from app.schemas.alertgroupschema import AlertGroupSchemaColumnCreate, AlertGroupSchemaColumnUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.alertgroup_schema import create_random_schema
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_alertgroup_schema(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alertgroup_schema = create_random_schema(faker, alertgroup.id, db)
    db_obj = crud.alert_group_schema.get(db, alertgroup_schema.id)

    assert db_obj.id == alertgroup_schema.id

    db_obj = crud.alert_group_schema.get(db, -1)

    assert db_obj is None


def test_get_multi_alertgroup_schema(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alertgroup_schemas = []
    for _ in range(5):
        alertgroup_schemas.append(create_random_schema(faker, alertgroup.id, db))

    db_objs = crud.alert_group_schema.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == alertgroup_schemas[0].id for i in db_objs)

    db_objs = crud.alert_group_schema.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == alertgroup_schemas[1].id for i in db_objs)

    db_objs = crud.alert_group_schema.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.alert_group_schema.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_alertgroup_schema(db: Session, faker: Faker) -> None:
    schema_type = faker.word()
    schema = AlertGroupSchemaColumnCreate(
        schema_key_name=f"{faker.word()}_{schema_type}",
        schema_key_type=schema_type,
        schema_key_order=0
    )
    db_obj = crud.alert_group_schema.create(db, obj_in=schema)

    assert db_obj.id is not None
    assert db_obj.schema_key_name == schema.schema_key_name
    assert db_obj.schema_key_type == schema.schema_key_type
    assert db_obj.schema_key_order == schema.schema_key_order

    with pytest.raises(ValidationError):
        schema_type = faker.word()
        schema = AlertGroupSchemaColumnCreate(
            schema_key_type=schema_type,
            schema_key_order=0
        )
        db_obj = crud.alert_group_schema.create(db, obj_in=schema)


def test_update_alertgroup_schema(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alertgroup_schema = create_random_schema(faker, alertgroup.id, db)
    schema_type = faker.word()
    update = AlertGroupSchemaColumnUpdate(
        alertgroup_id=alertgroup.id,
        schema_key_name=f"{faker.word()}_{schema_type}",
        schema_key_type=schema_type
    )

    db_obj = crud.alert_group_schema.update(db, db_obj=alertgroup_schema, obj_in=update)

    assert db_obj.id == alertgroup_schema.id
    assert db_obj.schema_key_name == update.schema_key_name
    assert db_obj.schema_key_type == update.schema_key_type

    schema_type = faker.word()
    update = {
        "alertgroup_id": alertgroup.id,
        "schema_key_name": f"{faker.word()}_{schema_type}",
        "schema_key_type": schema_type
    }

    db_obj = crud.alert_group_schema.update(db, db_obj=alertgroup_schema, obj_in=update)

    assert db_obj.id == alertgroup_schema.id
    assert db_obj.schema_key_name == update["schema_key_name"]
    assert db_obj.schema_key_type == update["schema_key_type"]

    schema_type = faker.word()
    update = {}

    db_obj = crud.alert_group_schema.update(db, db_obj=alertgroup_schema, obj_in=update)

    assert db_obj.id == alertgroup_schema.id

    schema_type = faker.word()
    update = {
        "test": "test"
    }

    db_obj = crud.alert_group_schema.update(db, db_obj=alertgroup_schema, obj_in=update)

    assert db_obj.id == alertgroup_schema.id
    assert not hasattr(db_obj, "test")

    schema_type = faker.word()
    update = {
        "alertgroup_id": alertgroup.id,
        "schema_key_name": f"{faker.word()}_{schema_type}",
        "schema_key_type": schema_type,
        "schema_key_order": 0
    }

    db_obj = crud.alert_group_schema.update(db, db_obj=AlertGroupSchemaKeys(), obj_in=update)

    assert db_obj.id == alertgroup_schema.id + 1
    assert db_obj.schema_key_name == update["schema_key_name"]
    assert db_obj.schema_key_type == update["schema_key_type"]


def test_remove_alertgroup_schema(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alertgroup_schema = create_random_schema(faker, alertgroup.id, db)

    db_obj = crud.alert_group_schema.remove(db, _id=alertgroup_schema.id)

    assert db_obj.id == alertgroup_schema.id

    db_obj_del = crud.alert_group_schema.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.alert_group_schema.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_alertgroup_schema(db: Session, faker: Faker) -> None:
    schema_type = faker.word()
    schema = AlertGroupSchemaColumnCreate(
        schema_key_name=f"{faker.word()}_{schema_type}",
        schema_key_type=schema_type,
        schema_key_order=0
    )

    db_obj = crud.alert_group_schema.get_or_create(db, obj_in=schema)

    assert db_obj.id is not None

    same_db_obj = crud.alert_group_schema.get_or_create(db, obj_in=schema)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_alertgroup_schema(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    schemas = []
    for _ in range(5):
        schemas.append(create_random_schema(faker, alertgroup.id, db))

    random_schema = random.choice(schemas)

    db_obj, count = crud.alert_group_schema.query_with_filters(db, filter_dict={"id": random_schema.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_schema.id

    db_obj, count = crud.alert_group_schema.query_with_filters(db, filter_dict={"alertgroup_id": alertgroup.id})

    assert db_obj is not None
    assert len(db_obj) == len(schemas)
    assert len(db_obj) == count
    assert all(a.alertgroup_id == alertgroup.id for a in db_obj)

    db_obj, count = crud.alert_group_schema.query_with_filters(db, filter_dict={"alertgroup_id": alertgroup.id}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(schemas) - 1
    assert len(db_obj) == count - 1
    assert all(a.alertgroup_id == alertgroup.id for a in db_obj)

    db_obj, count = crud.alert_group_schema.query_with_filters(db, filter_dict={"alertgroup_id": alertgroup.id}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.alertgroup_id == alertgroup.id for a in db_obj)

    db_obj, count = crud.alert_group_schema.query_with_filters(db, filter_dict={"schema_key_name": f"!{random_schema.schema_key_name}"})

    assert db_obj is not None
    assert all(a.schema_key_name != random_schema.schema_key_name for a in db_obj)


def test_get_with_roles_alertgroup_schema(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    schemas = []
    roles = []
    for _ in range(5):
        schema_type = faker.word()
        schema = AlertGroupSchemaColumnCreate(
            schema_key_name=f"{faker.word()}_{schema_type}",
            schema_key_type=schema_type,
            schema_key_order=0,
            alertgroup_id=alertgroup.id
        )
        role = create_random_role(db, faker)
        roles.append(role)

        schemas.append(crud.alert_group_schema.create_with_permissions(db, obj_in=schema, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.alert_group_schema.get_with_roles(db, [random_role])

    assert db_obj == []


def test_query_objects_with_roles_alert_group_schema(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    schemas = []
    roles = []
    for _ in range(5):
        schema_type = faker.word()
        schema = AlertGroupSchemaColumnCreate(
            schema_key_name=f"{faker.word()}_{schema_type}",
            schema_key_type=schema_type,
            schema_key_order=0,
            alertgroup_id=alertgroup.id
        )
        role = create_random_role(db, faker)
        roles.append(role)

        schemas.append(crud.alert_group_schema.create_with_permissions(db, obj_in=schema, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.alert_group_schema.get_with_roles(db, [random_role])

    assert db_obj == []


def test_create_with_owner_alertgroup_schema(db: Session, faker: Faker) -> None:
    schema_type = faker.word()
    schema = AlertGroupSchemaColumnCreate(
        schema_key_name=f"{faker.word()}_{schema_type}",
        schema_key_type=schema_type,
        schema_key_order=0
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.alert_group_schema.create_with_owner(db, obj_in=schema, owner=owner)

    assert db_obj is not None
    assert db_obj.schema_key_name == schema.schema_key_name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_alertgroup_schema(db: Session, faker: Faker) -> None:
    schema_type = faker.word()
    schema = AlertGroupSchemaColumnCreate(
        schema_key_name=f"{faker.word()}_{schema_type}",
        schema_key_type=schema_type,
        schema_key_order=0
    )
    role = create_random_role(db, faker)

    db_obj = crud.alert_group_schema.create_with_permissions(db, obj_in=schema, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.schema_key_name == schema.schema_key_name
    assert db_obj.schema_key_type == schema.schema_key_type
    assert db_obj.schema_key_order == schema.schema_key_order

    # no permission could be created with alert_group_schemas so nothing should be returned
    db_obj, count = crud.permission.query_with_filters(db, filter_dict={"target_id": db_obj.id})

    assert db_obj == []
    assert count == 0


def test_create_in_object_alertgroup_schema(db: Session, faker: Faker) -> None:
    schema_type = faker.word()
    schema = AlertGroupSchemaColumnCreate(
        schema_key_name=f"{faker.word()}_{schema_type}",
        schema_key_type=schema_type,
        schema_key_order=0
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.alert_group_schema.create_in_object(db, obj_in=schema, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.schema_key_name == schema.schema_key_name

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 0
    assert len(link) == 0


def test_get_history_alertgroup_schema(db: Session, faker: Faker) -> None:
    schema_type = faker.word()
    schema = AlertGroupSchemaColumnCreate(
        schema_key_name=f"{faker.word()}_{schema_type}",
        schema_key_type=schema_type,
        schema_key_order=0
    )
    user = create_random_user(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.alert_group_schema.create(db, obj_in=schema, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.alert_group_schema.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_alertgroup_schema(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    schema = create_random_schema(faker, alertgroup.id, db)
    user = create_random_user(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.alert_group_schema.remove(db, _id=schema.id, audit_logger=audit_logger)

    assert db_obj.id == schema.id

    db_obj = crud.alert_group_schema.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_alertgroup_schemas(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    schemas = []
    for _ in range(5):
        schemas.append(create_random_schema(faker, alertgroup.id, db))

    db_obj = crud.alert_group_schema.get_alertgroup_schemas(db, alertgroup.id)

    assert db_obj is not None
    assert db_obj != []
    assert len(db_obj) == len(schemas)
    assert any(i.id == schemas[0].id for i in db_obj)


def test_get_alertgroup_schema_map(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    schema = create_random_schema(faker, alertgroup.id, db)

    db_obj = crud.alert_group_schema.get_alertgroup_schema_map(db, alertgroup.id)

    assert db_obj is not None
    assert db_obj != {}
    assert db_obj == {schema.schema_key_name: schema.id}


def test_append_alertgroup_column(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    schema = create_random_schema(faker, alertgroup.id, db)

    new_column = faker.word()
    db_obj = crud.alert_group_schema.append_alertgroup_column(db, new_column, alertgroup.id)

    assert db_obj is not None
    assert db_obj.schema_key_name != schema.schema_key_name
    assert db_obj.schema_key_name == new_column
    assert db_obj.schema_key_order == schema.schema_key_order + 1
