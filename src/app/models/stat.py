from sqlalchemy import Column, Integer, Text

from app.db.base_class import Base


class Stat(Base):
    __tablename__ = "stats"

    id = Column("stat_id", Integer, primary_key=True)
    year = Column("stat_year", Integer, nullable=False)
    quarter = Column("stat_quarter", Integer, nullable=False)
    month = Column("stat_month", Integer, nullable=False)
    day_of_week = Column("stat_day_of_week", Integer, nullable=False)
    day = Column("stat_day", Integer, nullable=False)
    hour = Column("stat_hour", Integer, nullable=False)
    stat_metric = Column("stat_metric", Text, nullable=False)
    value = Column("stat_value", Integer, nullable=False)
