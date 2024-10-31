from sqlalchemy import Column, Enum, Integer

from app.db.base_class import Base
from app.enums import TargetTypeEnum
from app.models.mixins import TimestampMixin


class Promotion(Base, TimestampMixin):
    __tablename__ = "promotions"

    id = Column("promotion_id", Integer, primary_key=True)
    p0_id = Column("p0_id", Integer, nullable=False)
    p0_type = Column("p0_type", Enum(TargetTypeEnum), nullable=False)
    p1_id = Column("p1_id", Integer, nullable=False)
    p1_type = Column("p1_type", Enum(TargetTypeEnum), nullable=False)
