from sqlalchemy import Column, Enum, Integer, Text, text

from app.db.base_class import Base
from app.enums import TargetTypeEnum
from app.models.mixins import UTCDateTime


class Appearance(Base):
    __tablename__ = "appearances"

    id = Column("appearance_id", Integer, primary_key=True)
    when_date = Column(
        "when_date", UTCDateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    target_id = Column("target_id", Integer)
    target_type = Column("target_type", Enum(TargetTypeEnum))
    value_id = Column("value_id", Integer)
    value_type = Column("value_type", Text)
    value_str = Column("value_str", Text)
