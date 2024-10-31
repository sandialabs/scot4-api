from sqlalchemy import Column, Integer, JSON, VARCHAR, Text

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, SourceMixin, TagMixin


class ThreatModelItem(Base, TimestampMixin, SourceMixin, TagMixin):
    __tablename__ = "threat_model_items"

    id = Column("threat_model_id", Integer, primary_key=True, index=True)
    title = Column(VARCHAR(length=512), index=True)
    description = Column(Text)
    type = Column("threat_model_type", Text)
    data = Column("threat_model_data", JSON)
