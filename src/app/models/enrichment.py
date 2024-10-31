from sqlalchemy import Column, Enum, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.enums import EnrichmentClassEnum
from app.models.mixins import TimestampMixin


class Enrichment(Base, TimestampMixin):
    __tablename__ = "enrichments"
    id = Column("enrichment_id", Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.entity_id"))
    entity = relationship("Entity", back_populates="enrichments")
    title = Column("enrichment_title", Text, nullable=False)
    enrichment_class = Column("enrichment_class", Enum(EnrichmentClassEnum))
    data = Column("enrichment_data", JSON)
    description = Column("enrichment_description", Text)
