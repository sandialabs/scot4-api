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
    PopularityMixin,
    UserLinksMixin
)


class Event(
    Base,
    TimestampMixin,
    EntryMixin,
    FileCountMixin,
    TagMixin,
    SourceMixin,
    PromotionFromMixin,
    PromotionToMixin,
    PopularityMixin,
    UserLinksMixin
):
    __tablename__ = "events"

    id = Column("event_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False)
    tlp = Column("tlp", Enum(TlpEnum), nullable=False)
    status = Column("status", Enum(StatusEnum))
    subject = Column("subject", Text)
    view_count = Column("view_count", Integer, default=0, nullable=False)
    message_id = Column("message_id", Text, nullable=True)
