from sqlalchemy import JSON, Column, Enum, Text, Integer, VARCHAR

from app.db.base_class import Base
from app.enums import RemoteFlairStatusEnum
from app.models.mixins import TimestampMixin


class RemoteFlair(Base, TimestampMixin):
    __tablename__ = "remote_flairs"

    id = Column(Integer, primary_key=True)
    md5 = Column(VARCHAR(length=32), unique=True)  # cant by type text because MYSQL complains when trying to make it unique
    uri = Column(Text(length=2048))
    status = Column(Enum(RemoteFlairStatusEnum))
    results = Column(JSON)
