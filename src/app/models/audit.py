from datetime import datetime

from sqlalchemy import JSON, Column, Integer, Text

from app.db.base_class import Base
from app.models.mixins import UTCDateTime


class Audit(Base):
    __tablename__ = "audits"

    id = Column("audit_id", Integer, primary_key=True)
    when_date = Column(
        "when_date", UTCDateTime, nullable=False, default=datetime.utcnow
    )
    username = Column("username", Text)
    what = Column("what", Text, nullable=False)
    thing_type = Column("thing_type", Text)
    thing_subtype = Column("thing_subtype", Text)
    thing_id = Column("thing_id", Integer)
    src_ip = Column("src_ip", Text)
    user_agent = Column("user_agent", Text)
    audit_data_ver = Column("audit_data_ver", Text)
    audit_data = Column("audit_data", JSON)
