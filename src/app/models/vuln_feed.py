from sqlalchemy import Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import StatusEnum, TlpEnum
from app.models.mixins import (
    EntryMixin,
    FileCountMixin,
    PromotionFromMixin,
    PromotionToMixin,
    SourceMixin,
    TagMixin,
    TimestampMixin,
)


class VulnFeed(
    Base,
    TimestampMixin,
    EntryMixin,
    FileCountMixin,
    TagMixin,
    SourceMixin,
    PromotionFromMixin,
    PromotionToMixin,
):
    __tablename__ = "vuln_feeds"

    id = Column("vuln_feed_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False)
    tlp = Column("tlp", Enum(TlpEnum), nullable=False)
    status = Column("status", Enum(StatusEnum))
    subject = Column("subject", Text)
    view_count = Column("view_count", Integer, default=0, nullable=False)
    message_id = Column("message_id", Text, nullable=True)
