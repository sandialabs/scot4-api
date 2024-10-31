from sqlalchemy import JSON, Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import GuideStatusEnum, TlpEnum
from app.models.mixins import EntryMixin, TimestampMixin


class Guide(Base, TimestampMixin, EntryMixin):
    __tablename__ = "guides"

    id = Column("guide_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False, default="scot-admin")
    tlp = Column("tlp", Enum(TlpEnum), nullable=False, default="unset")
    subject = Column("subject", Text)
    status = Column(
        "status", Enum(GuideStatusEnum), nullable=False, default=GuideStatusEnum.current
    )
    application = Column("application", JSON)
    data_ver = Column("guide_data_ver", Text)
    data = Column("guide_data", JSON)
