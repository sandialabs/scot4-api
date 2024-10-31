from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, JSON, Text, Table, ForeignKey, \
    SmallInteger, VARCHAR
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, UTCDateTime, TimestampMixin


role_table = Table("users_roles", Base.metadata,
                   Column("username", VARCHAR(length=255), ForeignKey("users.username")),
                   Column("role_id", Integer, ForeignKey("roles.role_id"))
                   )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column("user_id", Integer, primary_key=True)
    username = Column("username", VARCHAR(length=255), unique=True, nullable=False)
    last_login = Column("last_login_date", UTCDateTime, default=datetime.utcnow)
    last_activity = Column("last_activity_date", UTCDateTime, default=datetime.utcnow)
    failed_attempts = Column("failed_attempt_count", SmallInteger, default=0)
    is_active = Column(Boolean(), default=True)
    pw_hash = Column("pwhash", Text)
    fullname = Column("fullname", Text)
    email = Column(VARCHAR(length=255), index=True)
    preferences = Column("preferences", JSON)
    is_superuser = Column(Boolean(), default=False)
    roles = relationship("Role", secondary=role_table, backref="users", lazy="joined")
