from sqlalchemy import Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import TargetTypeEnum
from app.models.mixins import TimestampMixin


class Link(Base, TimestampMixin):
    __tablename__ = "links"

    id = Column("link_id", Integer, primary_key=True)
    v0_type = Column("v0_type", Enum(TargetTypeEnum), nullable=False)
    v0_id = Column("v0_id", Integer, nullable=False)
    v1_type = Column("v1_type", Enum(TargetTypeEnum), nullable=False)
    v1_id = Column("v1_id", Integer, nullable=False)
    weight = Column("weight", Integer)
    context = Column("context", Text)
