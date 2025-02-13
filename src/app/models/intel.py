from sqlalchemy import Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import StatusEnum, TlpEnum
from app.models.mixins import (
    EntryMixin,
    FileCountMixin,
    SourceMixin,
    TagMixin,
    TimestampMixin,
    PromotionToMixin,
    PopularityMixin,
    UserLinksMixin
)


class Intel(Base, TimestampMixin, FileCountMixin, EntryMixin, TagMixin, SourceMixin, PromotionToMixin, PopularityMixin, UserLinksMixin):
    __tablename__ = "intels"

    id = Column("intel_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False, default="scot-admin")
    tlp = Column("tlp", Enum(TlpEnum), nullable=False, default="unset")
    subject = Column("subject", Text)
    status = Column("status", Enum(StatusEnum))
