from sqlalchemy import JSON, Column, Integer, Text

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Metric(Base, TimestampMixin):
    __tablename__ = "metrics"

    id = Column("metric_id", Integer, primary_key=True)
    name = Column("metric_name", Text)
    tooltip = Column("tooltip", Text)
    parameters = Column("results", JSON)