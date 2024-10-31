from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class AlertGroupSchemaKeys(Base):
    # This is like a column in an alert table
    __tablename__ = "alertgroup_schema_keys"

    id = Column("schema_key_id", Integer, primary_key=True)
    schema_key_name = Column("schema_key_name", Text)
    schema_key_type = Column("schema_key_type", Text)
    schema_key_order = Column("schema_key_order", Integer, nullable=False)
    alertgroup_id = Column("alertgroup_id", ForeignKey("alertgroups.alertgroup_id"))
    # Relationships
    alertgroup = relationship("AlertGroup", back_populates="alert_schema")
    data_cells = relationship("AlertData", back_populates="schema_column")
    # Relationship proxies to get data cell values
    data = association_proxy("data_cells", "data_value")
    data_flaired = association_proxy("data_cells", "data_value_flaired")
