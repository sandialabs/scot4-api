from sqlalchemy import Column, Integer, Text, ForeignKey, func, select
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from app.db.base_class import Base
from app.enums import TargetTypeEnum
from app.models.mixins import TimestampMixin
from app.models.link import Link

# https://docs.sqlalchemy.org/en/13/_modules/examples/generic_associations/table_per_related.html


class Tag(Base, TimestampMixin):
    __tablename__ = "tags"

    id = Column("tag_id", Integer, primary_key=True)
    name = Column("tag_name", Text, nullable=False)
    description = Column("description", Text)
    tag_type_id = Column(Integer, ForeignKey("tag_types.tag_type_id"))
    tag_type = relationship("TagType", back_populates="tags", lazy="selectin")
    type_name = association_proxy("tag_type", "name")
    type_description = association_proxy("tag_type", "description")

    @declared_attr
    def link_count(self):
        return column_property(
            select(func.count(Link.id))
            .where((Link.v1_type == TargetTypeEnum.tag) & (Link.v1_id == self.id))
            .correlate_except(Link)
            .scalar_subquery()
        )
