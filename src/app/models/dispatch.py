from sqlalchemy import Column, Enum, Integer, Text

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, TagMixin, SourceMixin, EntryMixin, PromotionToMixin, PopularityMixin, UserLinksMixin
from app.enums import StatusEnum, TlpEnum


class Dispatch(Base, TimestampMixin, TagMixin, SourceMixin, EntryMixin, PromotionToMixin, PopularityMixin, UserLinksMixin):
    __tablename__ = "dispatches"

    id = Column("dispatches_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False)
    tlp = Column("tlp", Enum(TlpEnum), nullable=False)
    subject = Column("subject", Text)
    status = Column("status", Enum(StatusEnum))
    message_id = Column("message_id", Text, nullable=True)
