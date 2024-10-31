from sqlalchemy import Column, Integer, JSON, Text, VARCHAR
from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class EntityClass(Base, TimestampMixin):
    __tablename__ = "entity_classes"
    id = Column("entity_class_id", Integer, primary_key=True)
    name = Column("entity_class_name", VARCHAR(length=320), unique=True)
    display_name = Column("entity_class_display_name", VARCHAR(length=320))
    description = Column("entity_class_description", Text)
    icon = Column("entity_icon", Text)
    data = Column("entity_class_data", JSON)
