from sqlalchemy import JSON, Boolean, Column, Enum, ForeignKey, Integer, Text, case, select
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base_class import Base
from app.enums import EntryClassEnum, TargetTypeEnum, TlpEnum
from app.models.mixins import TimestampMixin, SourceMixin, TagMixin, PopularityMixin, UserLinksMixin


class Entry(Base, TimestampMixin, SourceMixin, TagMixin, PopularityMixin, UserLinksMixin):
    __tablename__ = "entries"

    id = Column("entry_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False)
    tlp = Column("tlp", Enum(TlpEnum), nullable=False)
    parent_entry_id = Column("parent_entry_id", Integer, ForeignKey("entries.entry_id"))
    parent_entry = relationship(
        "Entry", back_populates="child_entries", uselist=False, remote_side=[id]
    )
    child_entries = relationship("Entry", back_populates="parent_entry", uselist=True)
    target_type = Column("target_type", Enum(TargetTypeEnum), nullable=False)
    target_id = Column("target_id", Integer, nullable=False)
    entry_class = Column("entryclass", Enum(EntryClassEnum))
    entry_data_ver = Column("entry_data_ver", Text)
    entry_data = Column("entry_data", JSON)
    parsed = Column("parsed", Boolean, nullable=False, default=False)

    parent_class_mapping = {}
    # Provides access to the "parent" by picking up the dynamically-created
    # relationship from EntryMixin
    # Performance isn't great, but we won't load this by default

    @hybrid_property
    def parent(self):
        return getattr(self, "parent_%s" % self.target_type.value, None)

    @hybrid_property
    def parent_subject(self):
        return getattr(self.parent, "subject", None)

    # Some slightly-evil case expression aggregation
    @parent_subject.expression
    def parent_subject(self):
        return case({k: select(v.subject).where(v.id == Entry.target_id).scalar_subquery()
                    for k, v in self.parent_class_mapping.items()},
                    value=Entry.target_type)
