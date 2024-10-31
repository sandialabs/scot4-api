from sqlalchemy import Column, Enum, Integer, Text, VARCHAR

from app.db.base_class import Base
from app.enums import TlpEnum
from app.models.mixins import SourceMixin, TagMixin, TimestampMixin


class File(Base, TimestampMixin, TagMixin, SourceMixin):
    __tablename__ = "files"
    id = Column("file_id", Integer, primary_key=True)
    file_pointer = Column("file_pointer", VARCHAR(length=70), unique=True, nullable=False)
    owner = Column("owner", Text, nullable=False)
    tlp = Column("tlp", Enum(TlpEnum), nullable=False)
    filename = Column("filename", Text)
    filesize = Column("filesize", Integer)
    sha256 = Column("sha256", Text)
    description = Column("description", Text)
    content_type = Column("content_type", Text)
