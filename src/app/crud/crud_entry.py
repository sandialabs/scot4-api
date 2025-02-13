from datetime import datetime
from typing import Any, Union

from sqlalchemy.orm import Session, aliased

from app.core.config import settings
from app.crud.base import CRUDBase
from app.crud.crud_entity import entity as entity_crud
from app.enums import PermissionEnum, TargetTypeEnum
from app.models.entry import Entry
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.schemas.entry import EntryCreate, EntryUpdate


class CRUDEntry(CRUDBase[Entry, EntryCreate, EntryUpdate]):
    # Custom filtering for entries
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "parent_subject")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)
        query = self._json_filter(query, filter_dict, "task_assignee", "assignee", "entry_data")
        query = self._json_filter(query, filter_dict, "task_status", "status", "entry_data")

        return super().filter(query, filter_dict)

    def remove(self, db_session: Session, *, _id: int, audit_logger=None):
        # Move all child entries to our parent entry
        obj = db_session.query(self.model).filter(self.model.id == _id).first()
        if obj is not None:
            for entry in obj.child_entries:
                entry.parent_entry_id = obj.parent_entry_id
                db_session.add(entry)
            db_session.flush()
            db_session.refresh(obj)
        return super().remove(db_session, _id=_id, audit_logger=audit_logger)

    def update(
        self,
        db_session: Session,
        *,
        db_obj: Entry,
        obj_in: Union[EntryUpdate, dict[str, Any]],
        audit_logger=None,
    ) -> Entry:
        # Update parent object's last modified time as well (if it has one)
        if db_obj.target_type in self.target_crud_mapping:
            parent_obj = self.target_crud_mapping[db_obj.target_type].get(
                db_session, db_obj.target_id
            )
            if parent_obj and hasattr(parent_obj, "modified"):
                parent_obj.modified = datetime.utcnow()
        return super().update(db_session, db_obj=db_obj, obj_in=obj_in, audit_logger=audit_logger)

    def get_by_type(
        self,
        db_session: Session,
        *,
        _id: int,
        _type: TargetTypeEnum,
        roles: list[Role] | None = None,
        skip: int = 0,
        limit: int = 100,
        audit_logger=None
    ) -> list[Entry]:
        """
        Get all entries (paginated) that are the children of the object of type
        _type and id _id
        """
        filter_dict = {"target_id": _id, "target_type": _type}
        return self.query_with_filters(
            db_session,
            roles=roles,
            filter_dict=filter_dict,
            skip=skip,
            limit=limit,
            audit_logger=audit_logger
        )

    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read
    ):
        """
        Entries are only accessible to users that can also access the parent
        object
        Note: admin permissions must be checked elsewhere
        """

        permission_alias = aliased(Permission)

        return db_session.query(self.model)\
            .join(Permission, (self.model.id == Permission.target_id))\
            .filter(((self.model.target_type_enum() == Permission.target_type) & (required_permission == Permission.permission)))\
            .filter(Permission.role_id.in_([role.id for role in roles] + [settings.EVERYONE_ROLE_ID]))\
            .join(permission_alias, self.model.target_id == permission_alias.target_id)\
            .filter(((self.model.target_type == permission_alias.target_type) & (required_permission == permission_alias.permission)))\
            .filter(permission_alias.role_id.in_([role.id for role in roles] + [settings.EVERYONE_ROLE_ID]))\
            .group_by(self.model.id)  # We can't use DISTINCT with entries

    def flair_update(
        self,
        db_session: Session,
        entry_id: int,
        text_flaired: str,
        entities: dict[str, list],
        text: str | None = None,
        text_plain: str | None = None,
        audit_logger=None
    ):
        entry = self.get(db_session, entry_id)
        if entry and entry.entry_data is not None:
            new_entry_data = dict(entry.entry_data)
            if text is not None:
                new_entry_data["html"] = text
            if text_plain is not None:
                new_entry_data["plain_text"] = text_plain
            new_entry_data["flaired_html"] = text_flaired
            new_entry_data["flaired"] = True
            entry_update = EntryUpdate(entry_data=new_entry_data, parsed=True)
            entry = self.update(
                db_session, db_obj=entry, obj_in=entry_update, audit_logger=audit_logger
            )
            for entity_type in entities:
                for entity in entities[entity_type]:
                    entity_crud.link_entity_by_value(
                        db_session,
                        entity_value=entity,
                        target_type=TargetTypeEnum.entry,
                        target_id=entry.id,
                        entity_type=entity_type,
                        audit_logger=audit_logger,
                    )
                    entity_crud.link_entity_by_value(
                        db_session,
                        entity_value=entity,
                        target_type=entry.target_type,
                        target_id=entry.target_id,
                        entity_type=entity_type,
                        audit_logger=audit_logger,
                    )
        return entry


entry = CRUDEntry(Entry)
