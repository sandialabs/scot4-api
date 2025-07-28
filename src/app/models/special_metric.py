from sqlalchemy import Column, Integer, Enum

from app.db.base_class import Base
from app.enums import TargetTypeEnum, SpecialMetricEnum
from app.models.mixins import TimestampMixin
from app.models.mixins import UTCDateTime


class SpecialMetric(Base, TimestampMixin):
    __tablename__ = "special_metrics"

    id = Column("special_metric_id", Integer, primary_key=True)
    target_id = Column("target_id", Integer, nullable=False)
    target_type = Column("target_type", Enum(TargetTypeEnum), nullable=False)
    metric_type = Column("metric_type", Enum(SpecialMetricEnum), nullable=False)
    start_time = Column("start_time", UTCDateTime, nullable=False)
    end_time = Column("end_time", UTCDateTime, nullable=False)