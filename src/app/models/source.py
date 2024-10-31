from sqlalchemy import Column, Integer, Text, VARCHAR

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id = Column("source_id", Integer, primary_key=True)
    name = Column("source_name", VARCHAR(length=300), nullable=False, unique=True)
    description = Column("description", Text)
