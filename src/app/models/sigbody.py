from sqlalchemy import Column, Integer, Text

from app.db.base_class import Base
from app.models.mixins import SourceMixin, TagMixin, TimestampMixin


class Sigbody(Base, TimestampMixin, TagMixin, SourceMixin):
    __tablename__ = "sigbodies"

    id = Column("sigbody_id", Integer, primary_key=True)
    revision = Column("revision", Integer)
    body = Column("body", Text)
    body64 = Column("body64", Text)
    signature_id = Column("signature_id", Integer)
