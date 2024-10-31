from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin

# https://docs.sqlalchemy.org/en/13/_modules/examples/generic_associations/table_per_related.html


class TagType(Base, TimestampMixin):
    __tablename__ = "tag_types"

    id = Column("tag_type_id", Integer, primary_key=True)
    name = Column("tag_type_name", Text, nullable=False)
    description = Column("description", Text)
    tags = relationship("Tag")
