from sqlalchemy import JSON, Column, Enum, Integer, Text

from app.db.base_class import Base
from app.enums import TlpEnum
from app.models.mixins import (
    EntryMixin,
    GuidesForMixin,
    SourceMixin,
    TagMixin,
    TimestampMixin,
    PopularityMixin,
    UserLinksMixin
)


class Signature(
    Base, TimestampMixin, EntryMixin, TagMixin, SourceMixin, GuidesForMixin, PopularityMixin, UserLinksMixin
):
    __tablename__ = "signatures"

    id = Column("signature_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False, default="scot-admin")
    tlp = Column("tlp_enum", Enum(TlpEnum), nullable=False, default="unset")
    latest_revision = Column("latest_revision", Integer, default=0)
    name = Column("signature_name", Text)
    description = Column("signature_description", Text)
    type = Column("signature_type", Text)
    status = Column("status", Text)
    stats = Column("stats", JSON)
    options = Column("options", JSON)
    data_ver = Column("signature_data_ver", Text)
    data = Column("signature_data", JSON)
