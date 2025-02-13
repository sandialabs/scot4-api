from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Annotated

from app.enums import AuthTypeEnum, StorageProviderEnum
from app.object_storage.base import BaseStorageProvider
from app.object_storage import storage_provider_classes


class SettingsBase(BaseModel):
    site_name: Annotated[str | None, Field(...)] = None
    environment_level: Annotated[str | None, Field(...)] = None
    it_contact: Annotated[EmailStr | None, Field(...)] = None
    time_zone: Annotated[str | None, Field(...)] = None
    default_permissions: Annotated[dict | None, Field(...)] = None


class SettingsCreate(SettingsBase):
    pass


class SettingsUpdate(SettingsBase):
    pass


class Settings(SettingsBase):
    id: Annotated[int, Field(...)]
    created: Annotated[datetime, Field(...)]
    modified: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class AuthSettingsBase(BaseModel):
    auth: Annotated[AuthTypeEnum | None, Field(..., examples=[a.value for a in list(AuthTypeEnum)])] = AuthTypeEnum.local
    auth_properties: Annotated[dict | None, Field(...)] = {}
    auth_active: Annotated[bool | None, Field(...)] = True


class AuthSettingsCreate(AuthSettingsBase):
    pass


class AuthSettingsUpdate(AuthSettingsBase):
    pass


class AuthSettings(AuthSettingsBase):
    id: Annotated[int | None, Field(...)] = None
    created: Annotated[datetime | None, Field(...)] = None
    modified: Annotated[datetime | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)


class AuthHelp(BaseModel):
    config_name_pretty: Annotated[dict[AuthTypeEnum, dict[str, str]], Field(..., examples=[{a.value: {"string": "string"}} for a in list(AuthTypeEnum)])]
    config_help: Annotated[dict[AuthTypeEnum, dict[str, str]], Field(..., examples=[])]


class StorageProviderSettingsBase(BaseModel):
    provider: Annotated[StorageProviderEnum, Field(..., examples=[a.value for a in list(StorageProviderEnum)])]
    config: Annotated[dict | None, Field(..., examples=[storage_provider_classes.get(a, BaseStorageProvider).config_help for a in list(StorageProviderEnum)])] = {}
    enabled: Annotated[bool | None, Field(...)] = False


class StorageProviderSettingsCreate(StorageProviderSettingsBase):
    pass


class StorageProviderSettingsUpdate(StorageProviderSettingsBase):
    provider: Annotated[StorageProviderEnum | None, Field(..., examples=[a.value for a in list(StorageProviderEnum)])] = None
    config: Annotated[dict | None, Field(..., examples=[storage_provider_classes.get(a, BaseStorageProvider).config_help for a in list(StorageProviderEnum)])] = None
    enabled: Annotated[bool | None, Field(...)] = None


class StorageProviderSettings(StorageProviderSettingsBase):
    id: Annotated[int | None, Field(...)] = None
    created: Annotated[datetime | None, Field(...)] = None
    modified: Annotated[datetime | None, Field(...)] = None

    model_config = ConfigDict(from_attributes=True)


class StorageProviderHelp(BaseModel):
    config_name_pretty: Annotated[dict[StorageProviderEnum, dict[str, str]], Field(..., examples=[storage_provider_classes.get(a, BaseStorageProvider).config_name_pretty for a in list(StorageProviderEnum)])]
    config_help: Annotated[dict[StorageProviderEnum, dict[str, str]], Field(..., examples=[storage_provider_classes.get(a, BaseStorageProvider).config_help for a in list(StorageProviderEnum)])]
