from sqlalchemy import Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import TlpEnum
from app.models.mixins import (
    EntryMixin,
    SourceMixin,
    TagMixin,
    TimestampMixin,
    FileCountMixin,
    PromotionFromMixin,
    PopularityMixin,
    UserLinksMixin
)


class Product(Base, TimestampMixin, EntryMixin, TagMixin, SourceMixin, FileCountMixin, PromotionFromMixin, PopularityMixin, UserLinksMixin):
    __tablename__ = "products"

    id = Column("products_id", Integer, primary_key=True, index=True)
    owner = Column("owner", Text, nullable=False, default="scot-admin")
    tlp = Column("tlp", Enum(TlpEnum), nullable=False, default="unset")
    subject = Column("subject", Text)
