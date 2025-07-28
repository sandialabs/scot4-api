from sqlalchemy import Column, Integer, ForeignKey, Enum, select
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import column_property, object_session, relationship
from app.db.base_class import Base
from app.models.mixins import TimestampMixin
from app.enums import UserLinkEnum, TargetTypeEnum


class UserLinks(Base, TimestampMixin):
    __tablename__ = "user_links"

    id = Column(Integer, primary_key=True)
    link_type = Column(Enum(UserLinkEnum), nullable=False)
    target_id = Column(Integer, nullable=False)
    target_type = Column(Enum(TargetTypeEnum), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.user_id"))
    entry_obj = relationship(
        "Entry", primaryjoin=f"and_(Entry.id == UserLinks.target_id, "
        f"UserLinks.target_type == '{TargetTypeEnum.entry.value}')",
        foreign_keys="UserLinks.target_id", lazy="joined"
    )
    parent_target_id = association_proxy("entry_obj", "target_id")
    parent_target_type = association_proxy("entry_obj", "target_type")

    @property
    def name(self):
        model = self.get_model_by_target_type(self.target_type)
        if model is not None:
            if self.target_type == TargetTypeEnum.entity:
                obj = object_session(self).scalar(select(model).where(model.id == self.target_id))
                if obj is not None:
                    return f"{obj.type_name}: {obj.value}"
            if hasattr(model, "subject"):
                obj = object_session(self).scalar(select(model).where(model.id == self.target_id))
                if obj is not None:
                    return obj.subject
            elif hasattr(model, "name"):
                obj = object_session(self).scalar(select(model).where(model.id == self.target_id))
                if obj is not None:
                    return obj.name

            if self.parent_target_type is not None:
                model = self.get_model_by_target_type(self.parent_target_type)
                if hasattr(model, "subject"):
                    obj = object_session(self).scalar(select(model).where(model.id == self.parent_target_id))
                    if obj is not None:
                        return obj.subject
                elif hasattr(model, "name"):
                    obj = object_session(self).scalar(select(model).where(model.id == self.parent_target_id))
                    if obj is not None:
                        return obj.name

        return None
