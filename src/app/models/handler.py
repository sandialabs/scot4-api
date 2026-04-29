from sqlalchemy import Column, Integer, Text

from app.db.base_class import Base, utc_now
from app.models.mixins import TimestampMixin, UTCDateTime


class Handler(Base, TimestampMixin):
    __tablename__ = "handlers"

    id = Column("handler_id", Integer, primary_key=True)
    start_date = Column(
        "start_date", UTCDateTime, default=utc_now, nullable=False
    )
    end_date = Column("end_date", UTCDateTime, default=utc_now, nullable=False)
    username = Column("username", Text, nullable=False)
    position = Column("position", Text)
