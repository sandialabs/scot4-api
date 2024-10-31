from typing import Any
from sqlalchemy import Column, Integer, JSON, Text, Enum, Table, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from app.enums import EntityStatusEnum, EntryClassEnum
from app.models.mixins import EntityCountMixin, TimestampMixin, EntryMixin, TagMixin, SourceMixin
from app.db.base_class import Base

association_table = Table(
    "entity_class_entity_association",
    Base.metadata,
    Column("entity_id", ForeignKey("entities.entity_id")),
    Column("entity_class_id", ForeignKey("entity_classes.entity_class_id")),
)


class Entity(Base, TimestampMixin, TagMixin, SourceMixin, EntityCountMixin, EntryMixin):
    __tablename__ = "entities"
    id = Column("entity_id", Integer, primary_key=True)
    classes = relationship("EntityClass", secondary=association_table, lazy="joined")
    status = Column("status", Enum(EntityStatusEnum), default=EntityStatusEnum.tracked)
    value = Column("entity_value", Text)
    type_id = Column(Integer, ForeignKey('entity_types.entity_type_id'))
    data_ver = Column("entity_data_ver", Text)
    data = Column("entity_data", JSON)
    entity_type = relationship("EntityType", back_populates="entities", lazy="joined")
    type_name = association_proxy("entity_type", "name")
    enrichments = relationship("Enrichment", back_populates="entity")

    @declared_attr
    def summaries(self):
        from app.models.entry import Entry  # Avoid circular dependency
        return relationship("Entry", foreign_keys=[Entry.target_id],
                            primaryjoin=(Entry.target_type == self.target_type_enum())
                            & (Entry.target_id == self.id) & (Entry.entry_class == EntryClassEnum.summary),
                            overlaps="entries", cascade="all", lazy="selectin")

    @hybrid_property
    def entry_annotation(self):
        if len(self.summaries) > 0 and self.summaries[0].entry_data is not None and self.summaries[0].entry_data.get('plain_text') is not None:
            annotation = self.summaries[0].entry_data['plain_text']
            return annotation
        elif self.entry_count > 0:
            if self.entries[0].entry_data is not None and self.entries[0].entry_data.get('plain_text') is not None:
                return self.entries[0].entry_data['plain_text']
        else:
            return None

    @hybrid_property
    def available_enrichments(self) -> dict[str, list[Any]]:
        enrichment_data = {}
        for enrichment in self.enrichments:
            if enrichment_data.get(enrichment.title) is None:
                enrichment_data[enrichment.title] = [enrichment]
            else:
                enrichment_data[enrichment.title].append(enrichment)
        # Now sort them descending
        for k, v in enrichment_data.items():
            v.sort(key=lambda x: x.modified, reverse=True)
        return enrichment_data
