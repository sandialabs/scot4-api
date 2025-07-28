from sqlalchemy import Column, Integer, Text, VARCHAR, func, select
from sqlalchemy.orm import column_property
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base
from app.models.mixins import TimestampMixin
from app.enums import TargetTypeEnum
from app.models.link import Link


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id = Column("source_id", Integer, primary_key=True)
    name = Column("source_name", VARCHAR(length=300), nullable=False, unique=True)
    description = Column("description", Text)

    @declared_attr
    def link_count(self):
        return column_property(
            select(func.count(Link.id))
            .where((Link.v1_type == TargetTypeEnum.tag) & (Link.v1_id == self.id))
            .correlate_except(Link)
            .scalar_subquery()
        )
