from sqlalchemy import Column, Integer, Text, JSON

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Settings(Base, TimestampMixin):
    """
    This holds settings for the RUNNING application.
    """

    __tablename__ = "settings"

    id = Column("settings_id", Integer, primary_key=True)
    site_name = Column("site_name", Text)
    environment_level = Column("env_level", Text)
    it_contact = Column("it_contact", Text)
    time_zone = Column("time_zone", Text)
    default_permissions = Column("default_permissions", JSON)
