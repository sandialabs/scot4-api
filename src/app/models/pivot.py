from sqlalchemy import Column, Integer, Text, ForeignKey, Table

from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.mixins import TimestampMixin
from sqlalchemy.ext.hybrid import hybrid_property


pivots_to_entity_types = Table(
    "pivots_entity_types",
    Base.metadata,
    Column("pivot_id", ForeignKey("pivots.pivot_id"), primary_key=True),
    Column("entity_type_id", ForeignKey("entity_types.entity_type_id"), primary_key=True),
)

pivots_to_entity_classes = Table(
    "pivots_entity_classes",
    Base.metadata,
    Column("pivot_id", ForeignKey("pivots.pivot_id"), primary_key=True),
    Column("entity_class_id", ForeignKey("entity_classes.entity_class_id"), primary_key=True),
)


class Pivot(Base, TimestampMixin):
    __tablename__ = "pivots"
    id = Column("pivot_id", Integer, primary_key=True)
    entity_types = relationship('EntityType', secondary=pivots_to_entity_types)
    entity_classes = relationship('EntityClass', secondary=pivots_to_entity_classes)
    template = Column("pivot_template", Text, nullable=False)
    title = Column("pivot_title", Text, nullable=False)
    description = Column("pivot_description", Text)

    @hybrid_property
    def linked_entity_type_count(self):
        return len(self.entity_types)

    @hybrid_property
    def linked_entity_class_count(self):
        return len(self.entity_classes)
