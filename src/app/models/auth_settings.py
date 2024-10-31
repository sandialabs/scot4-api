from sqlalchemy import JSON, Boolean, Column, Enum, ForeignKey, Integer, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_keyed_dict
from sqlalchemy.ext.associationproxy import association_proxy

from app.db.base_class import Base
from app.enums import AuthTypeEnum
from app.models.mixins import TimestampMixin

role_auth_table = Table(
    "roles_auth",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.role_id")),
    Column("settings_id", Integer, ForeignKey("auth_settings.auth_settings_id")),
)


class AuthStorage(Base):
    """
    This holds generic storage for authentication methods
    """
    __tablename__ = "auth_storage"

    id = Column("auth_storage_id", Integer, primary_key=True)
    key = Column("key", Text)
    value = Column("value", Text)
    auth_settings_id = Column(
        "auth_settings_id", Integer, ForeignKey("auth_settings.auth_settings_id")
    )


class AuthSettings(Base, TimestampMixin):
    """
    This holds authentication settins for the application.
    """
    __tablename__ = "auth_settings"

    id = Column("auth_settings_id", Integer, primary_key=True)
    auth = Column("auth", Enum(AuthTypeEnum))
    auth_properties = Column("auth_properties", JSON)
    auth_active = Column("auth_active", Boolean)
    # These are the roles that are linked to this set of auth settings
    # This means that membership in these roles is managed by these auth methods
    linked_roles = relationship(
        "Role", secondary=role_auth_table, cascade="all", backref="auth_methods"
    )
    _storage_nodes = relationship(
        "AuthStorage",
        collection_class=attribute_keyed_dict("key"),
        backref="auth_settings",
        cascade="all,delete-orphan"
    )
    storage = association_proxy("_storage_nodes", "value",
        creator=lambda k,v: AuthStorage(key=k, value=v))
