from sqlalchemy import JSON, Column, Integer, Text

from app.db.base_class import Base
from app.models.mixins import TimestampMixin


class Game(Base, TimestampMixin):
    __tablename__ = "games"

    id = Column("game_id", Integer, primary_key=True)
    name = Column("game_name", Text)
    tooltip = Column("tooltip", Text)
    parameters = Column("results", JSON)
