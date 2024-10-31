from sqlalchemy import Boolean, Column, Integer, ForeignKey, text, Enum, VARCHAR, Text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from app.db.base_class import Base
from app.enums import StatusEnum, TlpEnum
from app.models.mixins import PromotionToMixin, TimestampMixin
from app.models.permission import Permission

medium_text_length = 16777215


class Alert(Base, TimestampMixin, PromotionToMixin):
    __tablename__ = "alerts"

    id = Column("alert_id", Integer, primary_key=True)
    owner = Column("owner", VARCHAR(length=320), nullable=False, server_default="scot-admin")
    tlp = Column("tlp", Enum(TlpEnum), nullable=False, server_default="unset")
    status = Column("status", Enum(StatusEnum), nullable=False, server_default="open")
    parsed = Column("parsed", Boolean, nullable=False, server_default=text("FALSE"))
    alertgroup_id = Column(
        "alertgroup_id",
        Integer,
        ForeignKey("alertgroups.alertgroup_id"),
        nullable=False,
    )
    # Relationships
    permissions = relationship(
        "Permission",
        cascade="all,delete-orphan",
        primaryjoin=(
            (Permission.target_id == id) & (Permission.target_type == __tablename__)
        ),
        foreign_keys=Permission.target_id,
        lazy="noload",
    )
    alertgroup = relationship("AlertGroup", back_populates="alerts", lazy="selectin")
    data_cells = relationship(
        "AlertData",
        collection_class=attribute_mapped_collection("column_name"),
        cascade="all,delete-orphan", lazy="selectin"
    )
    # Association proxy: dict of {<column name>: <value>}
    alertgroup_subject = association_proxy("alertgroup", "subject")
    data = association_proxy("data_cells", "data_value")
    # Association proxy: dict of {<column name>: <flaired value>}
    data_flaired = association_proxy("data_cells", "data_value_flaired")


class AlertData(Base):
    # This is like a cell in a alert table
    __tablename__ = "alert_data"
    schema_key_id = Column("schema_key_id", Integer, ForeignKey("alertgroup_schema_keys.schema_key_id"), primary_key=True)
    alert_id = Column("alert_id", Integer, ForeignKey("alerts.alert_id"), primary_key=True)
    data_value = Column("data_value", Text(medium_text_length))
    data_value_flaired = Column("data_value_flaired", Text(medium_text_length))
    schema_key_id = Column(
        "schema_key_id",
        Integer,
        ForeignKey("alertgroup_schema_keys.schema_key_id"),
        primary_key=True,
    )
    alert_id = Column(
        "alert_id", Integer, ForeignKey("alerts.alert_id"), primary_key=True
    )
    # Row/column relationships
    schema_column = relationship(
        "AlertGroupSchemaKeys",
        back_populates="data_cells",
        lazy="joined"
    )
    alert = relationship("Alert", back_populates="data_cells")

    # Prepend underscores to column name if necessary
    @hybrid_property
    def column_name(self):
        # If a column name conflicts (or could), prepend an underscore
        protected_fields = ["id", "status", "promoted_ids"]
        key = self.schema_column.schema_key_name
        stripped_key = key.lstrip("_")
        if stripped_key in protected_fields:
            key = "_" + key
        return key
