# HOLD FOR > 4.0

from sqlalchemy import JSON, Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import TlpEnum
from app.models.mixins import TagMixin, TimestampMixin, PopularityMixin, UserLinksMixin


class Checklist(Base, TimestampMixin, TagMixin, PopularityMixin, UserLinksMixin):
    __tablename__ = "checklists"

    id = Column("checklist_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False)
    tlp = Column("tlp", Enum(TlpEnum), nullable=False)
    subject = Column("subject", Text)
    checklist_data_ver = Column("checklist_data_ver", Text)
    checklist_data = Column("checklist_data", JSON)
