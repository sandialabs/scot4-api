from sqlalchemy import Column, Integer, Text, VARCHAR
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id = Column("role_id", Integer, primary_key=True, index=True)
    name = Column("role_name", VARCHAR(length=255), nullable=False, unique=True)
    description = Column("description", Text)
    # Here for reference, but don't load for performance reasons
    # This should never be accessed, except when performing a cascade operation
    permissions = relationship("Permission", cascade="all,delete-orphan")
