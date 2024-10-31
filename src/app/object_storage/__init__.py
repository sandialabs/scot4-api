from app.enums import StorageProviderEnum
from .disk import DiskStorageProvider
from .dell_emc_s3 import DellEMCS3StorageProvider


storage_provider_classes = {
    StorageProviderEnum.disk: DiskStorageProvider,
    StorageProviderEnum.emc: DellEMCS3StorageProvider
}
