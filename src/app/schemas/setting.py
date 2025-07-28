from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Annotated

from app.enums import AuthTypeEnum, StorageProviderEnum
from app.object_storage.base import BaseStorageProvider
from app.object_storage import storage_provider_classes
from app.schemas.response import ResultBase


class SettingsBase(BaseModel):
    site_name: Annotated[str | None, Field(...)] = None
    environment_level: Annotated[str | None, Field(...)] = None
    it_contact: Annotated[EmailStr | None, Field(..., examples=["example@example.com"])] = None
    time_zone: Annotated[str | None, Field(..., description="The time zone of this SCOT instance", examples=["US/Mountain", "US/Central"])] = None
    default_permissions: Annotated[dict[str, dict[str, list[int]]] | None, Field(..., description="The global default permissions of newly-created objects, the top-level keys are object types (or \"default\" for all objects), the second-level keys are permissions, and the values are lists of role ids", examples=[{"event": {"read": [1, 3], "modify": [1], "delete": [1]}}])] = None


class SettingsCreate(SettingsBase):
    pass


class SettingsUpdate(SettingsBase):
    pass


class Settings(SettingsBase, ResultBase):
    model_config = ConfigDict(from_attributes=True)


class AuthSettingsBase(BaseModel):
    auth: Annotated[AuthTypeEnum, Field(..., description="The type of authentication to configure", examples=[a.value for a in list(AuthTypeEnum)])]
    auth_properties: Annotated[dict, Field(..., description="The configuration of your chosen authentication method")] = {}
    auth_active: Annotated[bool, Field(..., description="Whether users can use this authentication method to log in")] = True


class AuthSettingsCreate(AuthSettingsBase):
    pass


class AuthSettingsUpdate(AuthSettingsBase):
    auth: Annotated[AuthTypeEnum, Field(..., description="The type of authentication to configure", examples=[a.value for a in list(AuthTypeEnum)])] = None


class AuthSettings(AuthSettingsBase, ResultBase):
    model_config = ConfigDict(from_attributes=True)


class AuthHelp(BaseModel):
    config_name_pretty: Annotated[dict[AuthTypeEnum, dict[str, str]], Field(..., examples=[{a.value: {"string": "string"}} for a in list(AuthTypeEnum)])]
    config_help: Annotated[dict[AuthTypeEnum, dict[str, str]], Field(..., examples=[])]


class StorageProviderSettingsBase(BaseModel):
    provider: Annotated[StorageProviderEnum, Field(..., description="The type of storage to configure", examples=[a.value for a in list(StorageProviderEnum)])]
    config: Annotated[dict, Field(..., description="The configuration options of your chosen storage method", examples=[storage_provider_classes.get(a, BaseStorageProvider).config_help for a in list(StorageProviderEnum)])] = {}
    enabled: Annotated[bool, Field(..., description="Whether this storage method is what is used to store files (only one method should be active at a time)")] = False


class StorageProviderSettingsCreate(StorageProviderSettingsBase):
    pass


class StorageProviderSettingsUpdate(StorageProviderSettingsBase):
    provider: Annotated[StorageProviderEnum, Field(..., description="The type of storage to configure", examples=[a.value for a in list(StorageProviderEnum)])] = None


class StorageProviderSettings(StorageProviderSettingsBase, ResultBase):
    model_config = ConfigDict(from_attributes=True)


class StorageProviderHelp(BaseModel):
    config_name_pretty: Annotated[dict[StorageProviderEnum, dict[str, str]], Field(..., examples=[storage_provider_classes.get(a, BaseStorageProvider).config_name_pretty for a in list(StorageProviderEnum)])]
    config_help: Annotated[dict[StorageProviderEnum, dict[str, str]], Field(..., examples=[storage_provider_classes.get(a, BaseStorageProvider).config_help for a in list(StorageProviderEnum)])]
