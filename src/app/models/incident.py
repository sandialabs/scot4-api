from sqlalchemy import JSON, Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import StatusEnum, TlpEnum
from app.models.mixins import (
    EntryMixin,
    SourceMixin,
    TagMixin,
    TimestampMixin,
    UTCDateTime,
    FileCountMixin,
    PromotionFromMixin,
    PromotionToMixin,
    PopularityMixin,
    UserLinksMixin
)


class Incident(Base, TimestampMixin, EntryMixin, TagMixin, SourceMixin, FileCountMixin, PromotionFromMixin, PromotionToMixin, PopularityMixin, UserLinksMixin):
    __tablename__ = "incidents"

    id = Column("incident_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False)
    tlp = Column("tlp", Enum(TlpEnum), nullable=False)
    occurred_date = Column(
        "occurred_date", UTCDateTime, nullable=True
    )
    discovered_date = Column(
        "discovered_date", UTCDateTime, nullable=True
    )
    reported_date = Column(
        "reported_date", UTCDateTime, nullable=True
    )
    status = Column("status", Enum(StatusEnum), default="open")
    subject = Column("subject", Text)
    data_ver = Column("incident_data_ver", Text)
    data = Column("incident_data", JSON)
    view_count = Column("view_count", Integer, default=0)
