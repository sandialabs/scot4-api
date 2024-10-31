from datetime import datetime
from sqlalchemy import JSON, Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import TlpEnum
from app.models.mixins import TimestampMixin, UTCDateTime, EntryMixin


class Feed(Base, TimestampMixin, EntryMixin):
    __tablename__ = "feeds"

    id = Column("feed_id", Integer, primary_key=True)
    name = Column("feed_name", Text, nullable=False)
    owner = Column("owner", Text, nullable=False)
    tlp = Column("tlp", Enum(TlpEnum), nullable=False)
    status = Column("status", Text, nullable=False)
    type = Column("feed_type", Text, nullable=False)
    uri = Column("uri", Text, nullable=False)
    article_count = Column("article_count", Integer, nullable=False, default=0)
    promotions_count = Column("promotions_count", Integer, nullable=False, default=0)
    last_article = Column("last_article", UTCDateTime, default=datetime.utcnow)
    last_attempt = Column("last_attempt", UTCDateTime, default=datetime.utcnow)
    data = Column("feed_data", JSON)
