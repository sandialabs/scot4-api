from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import AuthTypeEnum, StorageProviderEnum
from app.schemas.setting import SettingsCreate, AuthSettingsCreate, StorageProviderSettingsCreate


def create_random_setting(db: Session, faker: Faker):
    setting = SettingsCreate(
        site_name=faker.word(),
        environment_level=faker.word(),
        it_contact=faker.email(),
        time_zone=faker.timezone()
    )

    return crud.setting.create(db, obj_in=setting)


def create_random_auth_setting(db: Session, faker: Faker):
    # keeping it to only local
    auth = AuthSettingsCreate(
        auth=AuthTypeEnum.local,
        auth_properties={
            "provider_name": faker.word()
        },
        auth_active=faker.pybool()
    )

    return crud.auth_setting.create_auth_method(db, auth)


def create_random_storage_provider(db: Session, faker: Faker):
    # keeping it to only local
    path = faker.file_path().rsplit("/", 1)[0]
    storage = StorageProviderSettingsCreate(
        provider=StorageProviderEnum.disk,
        config={
            "provider_name": faker.word(),
            "root_directory": path,
            "deleted_items_directory": f"{path}_deleted"
        },
        enabled=faker.pybool()
    )

    return crud.storage_setting.create(db, storage)


def reset_storage_settings(db: Session):
    # delete all but the first storage provider
    settings = crud.storage_setting.get_multi(db)
    for setting in settings:
        if setting.id == 1:
            continue
        crud.storage_setting.remove(db, _id=setting.id)
