from sqlalchemy import Column, VARCHAR

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class FeedType(Base, TimestampMixin):
    __tablename__ = "feed_types"

    type = Column("feed_type", VARCHAR(length=255), primary_key=True)
