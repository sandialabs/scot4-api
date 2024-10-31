from sqlalchemy import Column, Integer, JSON, Text, Enum, VARCHAR

from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.enums import EntityTypeStatusEnum
from app.models.mixins import TimestampMixin


class EntityType(Base, TimestampMixin):
    __tablename__ = "entity_types"

    id = Column("entity_type_id", Integer, primary_key=True)
    name = Column("entity_type_name", VARCHAR(length=300), unique=True)
    match_order = Column("match_order", Integer)  # Why have this has not nullable?
    status = Column("status", Enum(EntityTypeStatusEnum), nullable=False,
                    default=EntityTypeStatusEnum.active)
    options = Column("options", JSON)
    match = Column("match", Text)
    entity_type_data_ver = Column("entity_type_data_ver", Text)
    entity_type_data = Column("entity_type_data", JSON)
    entities = relationship("Entity")
