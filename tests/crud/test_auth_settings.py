import random
import pytest
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.auth import auth_classes
from app.enums import AuthTypeEnum
from app.schemas.setting import AuthSettingsCreate, AuthSettingsUpdate

from tests.utils.settings import create_random_auth_setting

# auth settings tests are separate because sometime in the future
# they will be in a different table with different curd methods


def test_create_auth_method(db: Session) -> None:
    # Test creating one of each type of auth
    new_settings = []
    for auth_type in AuthTypeEnum:
        settings = AuthSettingsCreate(auth=auth_type)
        new_auth = crud.auth_setting.create_auth_method(db, new_auth=settings)
        new_settings.append(new_auth)
        assert new_auth.auth == auth_type
        assert new_auth.auth_properties == auth_classes[auth_type].default_config
        assert new_auth.auth_active

    auth_methods = crud.auth_setting.get_auth_methods(db)
    random_auth = random.choice(new_settings)
    assert any(random_auth.id == i.id for i in auth_methods)


def test_remove_auth_method(db: Session, faker: Faker) -> None:
    setting = create_random_auth_setting(db, faker)

    db_obj = crud.auth_setting.remove_auth_method(db, setting.id)

    assert db_obj.id == setting.id

    settings = crud.auth_setting.get_auth_methods(db)

    assert db_obj.id not in [a.id for a in settings]

    # Can't remove the root settings object
    with pytest.raises(ValueError):
        crud.auth_setting.remove_auth_method(db, 1)

    db_obj = crud.auth_setting.remove_auth_method(db, -1)

    assert db_obj is None


def test_update_auth_method(db: Session, faker: Faker) -> None:
    setting = create_random_auth_setting(db, faker)
    update = AuthSettingsUpdate(
        auth=AuthTypeEnum.ldap,
        auth_properties={"dummy_setting": False},
        auth_active=False,
    )

    db_obj = crud.auth_setting.update_auth_method(db, setting.id, update)

    assert setting.id == db_obj.id
    assert setting.auth == update.auth
    assert setting.auth_properties == update.auth_properties
    assert setting.auth_active == update.auth_active


def test_get_auth_help() -> None:
    help_obj = crud.auth_setting.get_auth_help()

    assert help_obj is not None
    assert "config_name_pretty" in help_obj.keys()
    assert "config_help" in help_obj.keys()
    assert AuthTypeEnum.aad.value in help_obj["config_help"].keys()
    assert AuthTypeEnum.local.value in help_obj["config_help"].keys()
    assert AuthTypeEnum.ldap.value in help_obj["config_help"].keys()
