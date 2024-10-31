from sqlalchemy import Column, Enum, ForeignKey, Integer

from app.db.base_class import Base
from app.enums import PermissionEnum, TargetTypeEnum


class Permission(Base):
    __tablename__ = "object_permissions"

    id = Column("object_permission_id", Integer, primary_key=True, index=True)
    role_id = Column("role_id", Integer, ForeignKey("roles.role_id"))
    target_type = Column("target_type", Enum(TargetTypeEnum), nullable=False)
    target_id = Column("target_id", Integer, nullable=False)
    permission = Column("permission", Enum(PermissionEnum), nullable=False)
