from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.storage_settings import StorageSettings
from app.object_storage import storage_provider_classes
from app.schemas.setting import (
    StorageProviderSettings,
    StorageProviderSettingsCreate,
    StorageProviderSettingsUpdate,
)


class CRUDStorageSetting(
    CRUDBase[
        StorageProviderSettings,
        StorageProviderSettingsCreate,
        StorageProviderSettingsUpdate,
    ]
):
    def create(
        self,
        db_session: Session,
        new_storage_provider: StorageProviderSettingsCreate,
        audit_logger=None,
    ) -> StorageSettings:
        new_db_obj = StorageSettings()
        new_db_obj.config = new_storage_provider.config
        # Set auth_properties to default if not explicitly set
        _ = new_storage_provider.model_dump(exclude_unset=True).keys()
        storage_provider_class = storage_provider_classes[new_storage_provider.provider]
        if new_db_obj.config == {} or new_db_obj.config is None:
            new_db_obj.config = storage_provider_class.default_config
        new_db_obj.enabled = new_storage_provider.enabled
        new_db_obj.provider = new_storage_provider.provider
        if audit_logger is not None:
            audit_logger.log("create", new_db_obj)
        db_session.add(new_db_obj)
        db_session.flush()
        db_session.refresh(new_db_obj)

        return new_db_obj

    def update(
        self,
        db_session: Session,
        _id: int,
        updated_storage_provider: StorageProviderSettingsUpdate,
        audit_logger=None,
    ) -> StorageSettings:
        update_db_obj = self.get(db_session=db_session, _id=_id)
        if update_db_obj is None:
            return None
        if updated_storage_provider.config is not None:
            update_db_obj.config = updated_storage_provider.config
        if updated_storage_provider.enabled is not None:
            if updated_storage_provider.enabled is True:
                no_enabled_storage_provider = (
                    self.query_with_filters(
                        db_session=db_session, filter_dict={"enabled": True}
                    )[1]
                    == 0
                )
                if no_enabled_storage_provider is True:
                    update_db_obj.enabled = updated_storage_provider.enabled
                else:
                    pass
            else:
                update_db_obj.enabled = updated_storage_provider.enabled
        if audit_logger is not None:
            audit_logger.log("update", update_db_obj)
        db_session.add(update_db_obj)
        db_session.flush()
        db_session.refresh(update_db_obj)
        return update_db_obj

    def get_storage_provider_help(self) -> dict:
        pretty_names = {
            provider.value: storage_provider_classes[provider].config_name_pretty
            for provider in storage_provider_classes
        }
        config_help = {
            provider.value: storage_provider_classes[provider].config_help
            for provider in storage_provider_classes
        }
        return {"config_name_pretty": pretty_names, "config_help": config_help}


storage_setting = CRUDStorageSetting(StorageSettings)
