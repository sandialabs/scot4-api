from sqlalchemy import Column, Enum, Integer, Text, func, select
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, column_property

from app.db.base_class import Base
from app.enums import StatusEnum, TlpEnum
from app.models.alert import Alert
from app.models.alertgroupschema import AlertGroupSchemaKeys
from app.models.mixins import (
    SignatureForMixin,
    SourceMixin,
    TagMixin,
    TimestampMixin,
    UTCDateTime,
    PopularityMixin,
    UserLinksMixin
)


class AlertGroup(Base, TimestampMixin, SourceMixin, TagMixin, SignatureForMixin, PopularityMixin, UserLinksMixin):
    __tablename__ = "alertgroups"

    id = Column("alertgroup_id", Integer, primary_key=True)
    owner = Column("owner", Text, nullable=False, default="scot-admin")
    tlp = Column("tlp", Enum(TlpEnum), default=TlpEnum.unset)
    view_count = Column("view_count", Integer, default=0)
    first_view = Column("firstview_date", UTCDateTime)
    message_id = Column("message_id", Text)
    subject = Column("subject", Text)
    back_refs = Column("backrefs", Text)
    # Relationships to rows (alerts) and columns (alertgroupschemas)
    alerts = relationship(
        "Alert", back_populates="alertgroup", cascade="all,delete-orphan"
    )
    alert_schema = relationship(
        "AlertGroupSchemaKeys",
        back_populates="alertgroup",
        cascade="all,delete-orphan",
        order_by=AlertGroupSchemaKeys.schema_key_order,
    )
    # Association proxies
    alert_data = association_proxy("alerts", "data")
    alert_ids = association_proxy("alerts", "id")
    alert_status = association_proxy("alerts", "status")
    alert_data_flaired = association_proxy("alerts", "data_flaired")
    column_names = association_proxy("alert_schema", "schema_key_name")
    column_types = association_proxy("alert_schema", "schema_key_type")

    @declared_attr
    def alert_count(self):
        return column_property(
            select(func.count(Alert.id))
            .where(Alert.alertgroup_id == self.id)
            .scalar_subquery()
        )

    @declared_attr
    def open_count(self):
        return column_property(
            select(func.count(Alert.id))
            .where(
                (Alert.alertgroup_id == self.id)
                & (Alert.status == StatusEnum.open)
            )
            .scalar_subquery()
        )

    @declared_attr
    def closed_count(self):
        return column_property(
            select(func.count(Alert.id))
            .where(
                (Alert.alertgroup_id == self.id)
                & (Alert.status == StatusEnum.closed)
            )
            .scalar_subquery()
        )

    @declared_attr
    def promoted_count(self):
        return column_property(
            select(func.count(Alert.id))
            .where(
                (Alert.alertgroup_id == self.id)
                & (Alert.status == StatusEnum.promoted)
            )
            .scalar_subquery()
        )

    @hybrid_property
    def full_column_names(self):
        ret_arr = ["id", "status", "promoted_ids"]
        if self.alerts:
            # If a column name conflicts, prepend an underscore
            for name in self.column_names:
                while name in ret_arr:
                    name = "_" + name
                ret_arr.append(name)
        ret_arr.remove("promoted_ids")  # This key was only to remove duplicates
        return ret_arr

    @hybrid_property
    def associated_sig_guide_map(self):
        ret_obj = {}
        if self.associated_signatures:
            for sig in self.associated_signatures:
                ret_obj[sig.id] = [x.id for x in sig.associated_guides]
        return ret_obj

    @hybrid_property
    def full_column_types(self):
        ret_arr = ["number", "string"]
        if self.alerts:
            ret_arr.extend(self.column_types)
        return ret_arr

    @hybrid_property
    def full_alert_data(self):
        ret_arr = []
        if self.alert_data and self.alert_ids and self.alert_status:
            for x in range(self.alert_count):
                ret_obj = {}
                ret_obj["id"] = self.alert_ids[x]
                ret_obj["status"] = self.alert_status[x]
                ret_obj["promoted_ids"] = [
                    x.p1_id for x in self.alerts[x].promoted_to_targets
                ]
                # If a column name conflicts, prepend an underscore
                for key, data in self.alert_data[x].items():
                    while key in ret_obj:
                        key = "_" + key
                    ret_obj[key] = data
                ret_arr.append(ret_obj)
        return ret_arr

    @hybrid_property
    def full_alert_data_flaired(self):
        ret_arr = []
        if self.alert_data and self.alert_ids and self.alert_status:
            for x in range(self.alert_count):
                ret_obj = {}
                ret_obj["id"] = self.alert_ids[x]
                ret_obj["status"] = self.alert_status[x]
                ret_obj["promoted_ids"] = [
                    x.p1_id for x in self.alerts[x].promoted_to_targets
                ]
                # If a column name conflicts, prepend an underscore
                for key, data in self.alert_data_flaired[x].items():
                    while key in ret_obj:
                        key = "_" + key
                    ret_obj[key] = data
                ret_arr.append(ret_obj)
        return ret_arr
