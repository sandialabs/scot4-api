from sqlalchemy import JSON, Boolean, Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import StorageProviderEnum
from app.models.mixins import TimestampMixin


class StorageSettings(Base, TimestampMixin):
    """
    This holds settings for the storage provider for the instance
    """

    __tablename__ = "storage_settings"
    id = Column("storage_settings_id", Integer, primary_key=True)
    name = Column("storage_provider_name", Text)
    provider = Column("storage_provider", Enum(StorageProviderEnum))
    config = Column("storage_config", JSON)
    enabled = Column("enabled", Boolean)
