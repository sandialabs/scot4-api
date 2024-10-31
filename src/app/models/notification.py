from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    id = Column("notification_id", Integer, primary_key=True)
    user_id = Column("user_id", ForeignKey("users.user_id"))
    user = relationship("User")
    message = Column("notification_message", Text, nullable=False)
    ack = Column("notification_ack", Boolean, nullable=False)
    ref_id = Column("ref_id", Text, nullable=True)
