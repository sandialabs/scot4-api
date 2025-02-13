import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Settings
from app.schemas.setting import SettingsCreate, SettingsUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.settings import create_random_setting
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_setting(db: Session) -> None:
    db_obj = crud.setting.get(db)

    assert db_obj.id == 1


def test_get_multi_setting(db: Session, faker: Faker) -> None:
    settings = []
    for _ in range(5):
        settings.append(create_random_setting(db, faker))

    db_objs = crud.setting.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == settings[0].id for i in db_objs)

    db_objs = crud.setting.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == settings[1].id for i in db_objs)

    db_objs = crud.setting.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.setting.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_setting(db: Session, faker: Faker) -> None:
    setting = SettingsCreate(
        site_name=faker.word(),
        environment_level=faker.word(),
        it_contact=faker.email(),
        time_zone=faker.timezone()
    )
    db_obj = crud.setting.create(db, obj_in=setting)

    assert db_obj.id is not None
    assert db_obj.site_name == setting.site_name
    assert db_obj.environment_level == setting.environment_level
    assert db_obj.it_contact == setting.it_contact
    assert db_obj.time_zone == setting.time_zone


def test_update_setting(db: Session, faker: Faker) -> None:
    setting = create_random_setting(db, faker)
    update = SettingsUpdate(
        site_name=faker.word(),
        environment_level=faker.word(),
        it_contact=faker.email(),
        time_zone=faker.timezone()
    )

    db_obj = crud.setting.update(db, db_obj=setting, obj_in=update)

    assert db_obj.id == setting.id
    assert db_obj.site_name == update.site_name
    assert db_obj.environment_level == update.environment_level
    assert db_obj.it_contact == update.it_contact
    assert db_obj.time_zone == update.time_zone

    update = {}

    db_obj = crud.setting.update(db, db_obj=setting, obj_in=update)

    assert db_obj.id == setting.id

    update = {
        "test": "test"
    }

    db_obj = crud.setting.update(db, db_obj=setting, obj_in=update)

    assert db_obj.id == setting.id
    assert not hasattr(db_obj, "test")

    update = {
        "site_name": faker.word(),
        "environment_level": faker.word(),
        "it_contact": faker.email(),
        "time_zone": faker.timezone()
    }

    db_obj = crud.setting.update(db, db_obj=Settings(), obj_in=update)

    assert db_obj.id == setting.id + 1
    assert db_obj.site_name == update["site_name"]
    assert db_obj.environment_level == update["environment_level"]
    assert db_obj.it_contact == update["it_contact"]
    assert db_obj.time_zone == update["time_zone"]


def test_remove_setting(db: Session, faker: Faker) -> None:
    setting = create_random_setting(db, faker)

    db_obj = crud.setting.remove(db, _id=setting.id)

    assert db_obj.id == setting.id

    db_obj = crud.setting.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_setting(db: Session, faker: Faker) -> None:
    setting = SettingsCreate(
        site_name=faker.word(),
        environment_level=faker.word(),
        it_contact=faker.email(),
        time_zone=faker.timezone()
    )

    db_obj = crud.setting.get_or_create(db, obj_in=setting)

    assert db_obj.id is not None

    same_db_obj = crud.setting.get_or_create(db, obj_in=setting)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_setting(db: Session, faker: Faker) -> None:
    settings = []
    for _ in range(5):
        settings.append(create_random_setting(db, faker))

    random_setting = random.choice(settings)

    db_obj, count = crud.setting.query_with_filters(db, filter_dict={"id": random_setting.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_setting.id

    db_obj, count = crud.setting.query_with_filters(db, filter_dict={"site_name": f"!{random_setting.site_name}"})

    assert db_obj is not None
    assert all(a.site_name != random_setting.site_name for a in db_obj)


def test_get_with_roles_setting(db: Session, faker: Faker) -> None:
    settings = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        setting = SettingsCreate(
            site_name=faker.word(),
            environment_level=faker.word(),
            it_contact=faker.email(),
            time_zone=faker.timezone()
        )
        roles.append(role)

        settings.append(crud.setting.create_with_permissions(db, obj_in=setting, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.setting.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_setting(db: Session, faker: Faker) -> None:
    settings = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        setting = SettingsCreate(
            site_name=faker.word(),
            environment_level=faker.word(),
            it_contact=faker.email(),
            time_zone=faker.timezone()
        )
        roles.append(role)

        settings.append(crud.setting.create_with_permissions(db, obj_in=setting, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.setting.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_setting(db: Session, faker: Faker) -> None:
    setting = SettingsCreate(
        site_name=faker.word(),
        environment_level=faker.word(),
        it_contact=faker.email(),
        time_zone=faker.timezone()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.setting.create_with_owner(db, obj_in=setting, owner=owner)

    assert db_obj is not None
    assert db_obj.site_name == setting.site_name
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_setting(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    setting = SettingsCreate(
        site_name=faker.word(),
        environment_level=faker.word(),
        it_contact=faker.email(),
        time_zone=faker.timezone()
    )

    db_obj = crud.setting.create_with_permissions(db, obj_in=setting, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.site_name == setting.site_name
    assert db_obj.environment_level == setting.environment_level
    assert db_obj.it_contact == setting.it_contact
    assert db_obj.time_zone == setting.time_zone


def test_create_in_object_setting(db: Session, faker: Faker) -> None:
    setting = SettingsCreate(
        site_name=faker.word(),
        environment_level=faker.word(),
        it_contact=faker.email(),
        time_zone=faker.timezone()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.setting.create_in_object(db, obj_in=setting, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.site_name == setting.site_name

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v0_target": TargetTypeEnum.alertgroup, "v1_id": db_obj.id})

    assert count == 0
    assert len(link) == 0


def test_get_history_setting(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    setting = SettingsCreate(
        site_name=faker.word(),
        environment_level=faker.word(),
        it_contact=faker.email(),
        time_zone=faker.timezone()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.setting.create(db, obj_in=setting, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.setting.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_setting(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    setting = create_random_setting(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.setting.remove(db, _id=setting.id, audit_logger=audit_logger)

    assert db_obj.id == setting.id

    db_obj = crud.setting.undelete(db, db_obj.id)

    assert db_obj is None
