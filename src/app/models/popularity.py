from sqlalchemy import Column, Enum, Integer, UniqueConstraint, ForeignKey

from app.db.base_class import Base
from app.enums import TargetTypeEnum, PopularityMetricEnum
from app.models.mixins import TimestampMixin


class Popularity(Base, TimestampMixin):
    __tablename__ = "popularity"
    # make sure that we only get one target and owner combination as a user cant upvote and downvote the same target
    # or have two upvotes/downvotes
    __table_args__ = (UniqueConstraint('target_type', 'target_id', 'owner_id', name='unique_target_owner'),)

    id = Column(Integer, primary_key=True)
    target_type = Column(Enum(TargetTypeEnum), nullable=False)
    target_id = Column(Integer, nullable=False)
    metric_type = Column(Enum(PopularityMetricEnum), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.user_id"))
