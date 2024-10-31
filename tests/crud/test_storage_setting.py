import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import StorageProviderEnum
from app.schemas.setting import StorageProviderSettingsCreate, StorageProviderSettingsUpdate

from tests.utils.settings import create_random_storage_provider
from tests.utils.user import create_random_user


def test_get_setting(db: Session, faker: Faker) -> None:
    setting = create_random_storage_provider(db, faker)
    db_obj = crud.storage_setting.get(db, setting.id)

    assert db_obj.id == setting.id

    db_obj = crud.storage_setting.get(db, -1)

    assert db_obj is None


def test_get_multi_setting(db: Session, faker: Faker) -> None:
    settings = []
    for _ in range(5):
        settings.append(create_random_storage_provider(db, faker))

    db_objs = crud.storage_setting.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == settings[0].id for i in db_objs)

    db_objs = crud.storage_setting.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == settings[1].id for i in db_objs)

    db_objs = crud.storage_setting.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.storage_setting.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_setting(db: Session, faker: Faker) -> None:
    path = faker.file_path().rsplit("/", 1)[0]
    setting = StorageProviderSettingsCreate(
        provider=StorageProviderEnum.disk,
        config={
            "provider_name": faker.word(),
            "root_directory": path,
            "deleted_items_directory": f"{path}_deleted"
        },
        enabled=faker.pybool()
    )
    db_obj = crud.storage_setting.create(db, new_storage_provider=setting)

    assert db_obj.id is not None
    assert db_obj.provider == setting.provider
    assert db_obj.config == setting.config
    assert db_obj.enabled == setting.enabled


def test_update_setting(db: Session, faker: Faker) -> None:
    setting = create_random_storage_provider(db, faker)
    path = faker.file_path().rsplit("/", 1)[0]
    update = StorageProviderSettingsUpdate(
        provider=StorageProviderEnum.disk,
        config={
            "provider_name": faker.word(),
            "root_directory": path,
            "deleted_items_directory": f"{path}_deleted"
        },
        enabled=faker.pybool()
    )

    db_obj = crud.storage_setting.update(db, setting.id, update)

    assert db_obj.id == setting.id
    assert db_obj.provider == update.provider
    assert db_obj.config == update.config


def test_remove_setting(db: Session, faker: Faker) -> None:
    setting = create_random_storage_provider(db, faker)

    db_obj = crud.storage_setting.remove(db, _id=setting.id)

    assert db_obj.id == setting.id

    db_obj_del = crud.storage_setting.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.storage_setting.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_setting(db: Session, faker: Faker) -> None:
    path = faker.file_path().rsplit("/", 1)[0]
    setting = StorageProviderSettingsCreate(
        provider=StorageProviderEnum.disk,
        config={
            "provider_name": faker.word(),
            "root_directory": path,
            "deleted_items_directory": f"{path}_deleted"
        },
        enabled=faker.pybool()
    )

    db_obj = crud.storage_setting.get_or_create(db, obj_in=setting)

    assert db_obj.id is not None

    same_db_obj = crud.storage_setting.get_or_create(db, obj_in=setting)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_setting(db: Session, faker: Faker) -> None:
    settings = []
    for _ in range(5):
        settings.append(create_random_storage_provider(db, faker))

    random_setting = random.choice(settings)

    db_obj, count = crud.storage_setting.query_with_filters(db, filter_dict={"id": random_setting.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_setting.id


def test_get_history_setting(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    path = faker.file_path().rsplit("/", 1)[0]
    setting = StorageProviderSettingsCreate(
        provider=StorageProviderEnum.disk,
        config={
            "provider_name": faker.word(),
            "root_directory": path,
            "deleted_items_directory": f"{path}_deleted"
        },
        enabled=faker.pybool()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.storage_setting.create(db, new_storage_provider=setting, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.storage_setting.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_setting(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    setting = create_random_storage_provider(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.storage_setting.remove(db, _id=setting.id, audit_logger=audit_logger)

    assert db_obj.id == setting.id

    db_obj = crud.storage_setting.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_auth_help() -> None:
    help_obj = crud.storage_setting.get_storage_provider_help()

    assert help_obj is not None
    assert "config_name_pretty" in help_obj.keys()
    assert "config_help" in help_obj.keys()
    assert StorageProviderEnum.disk.value in help_obj["config_help"].keys()
    assert StorageProviderEnum.emc.value in help_obj["config_help"].keys()
