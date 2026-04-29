from sqlalchemy import Column, Integer, JSON, Text, Enum

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, SourceMixin, TagMixin, EntryMixin, UserLinksMixin, PopularityMixin
from app.enums import ThreatModelName


class ThreatModelItem(Base, TimestampMixin, SourceMixin, TagMixin, EntryMixin, UserLinksMixin, PopularityMixin):
    __tablename__ = "threat_model_items"

    id = Column(Integer, primary_key=True, index=True)
    threat_model_name = Column(Enum(ThreatModelName))
    threat_model_id = Column(Text)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    owner = Column(Text, nullable=False, default="scot-admin")
    data = Column(JSON)
