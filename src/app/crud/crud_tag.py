from datetime import datetime
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.crud.crud_appearance import appearance
from app.crud.crud_link import link
from app.enums import TargetTypeEnum, PermissionEnum
from app.models.link import Link
from app.models.tag import Tag
from app.models.role import Role
from app.schemas.appearance import AppearanceCreate
from app.schemas.tag import TagCreate, TagUpdate


class CRUDTag(CRUDBase[Tag, TagCreate, TagUpdate]):
    def get_by_name(self, db_session: Session, tag_name: str):
        query = db_session.query(Tag).filter(Tag.name == tag_name.lower())
        query = query.order_by(Tag.id)
        return query.first()   # Return tag with lowest id if there's multiple

    # All tags are inherently queryable by anyone

    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read,
    ):
        return db_session.query(self.model)

    # Custom filtering for tags
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "name", True)
        query = self._str_filter(query, filter_dict, "description")

        return super().filter(query, filter_dict)

    def assign(
        self,
        db_session: Session,
        tag_id: int,
        target_type: TargetTypeEnum,
        target_id: int,
        audit_logger=None,
    ):
        """
        Assigns a tag to an object by tag id; the existence of the object
        is NOT checked.
        """
        # Make sure tag exists (use session cache)
        tag = db_session.get(Tag, tag_id)
        if tag is None:
            return None
        # Ensure that the object is not already tagged with this tag
        existing = (
            db_session.query(Link)
            .filter(
                (Link.v0_type == target_type)
                & (Link.v0_id == target_id)
                & (Link.v1_type == TargetTypeEnum.tag)
                & (Link.v1_id == tag_id)
            )
            .first()
        )
        if not existing:
            # Do the actual tagging
            new_link = {
                "v0_type": target_type,
                "v0_id": target_id,
                "v1_type": TargetTypeEnum.tag,
                "v1_id": tag_id,
                "weight": 1,
                "context": "tagged",
            }
            link.create(db_session, obj_in=new_link, audit_logger=audit_logger)
            # Add to appearances table
            new_appearance = AppearanceCreate(
                when_date=datetime.utcnow(),
                target_type=target_type,
                target_id=target_id,
                value_type=TargetTypeEnum.tag.value,
                value_id=tag_id,
                value_str=tag.name,
            )
            appearance.create(
                db_session, obj_in=new_appearance, audit_logger=audit_logger
            )
        return tag

    def assign_by_name(
        self,
        db_session: Session,
        tag_name: str,
        target_type: TargetTypeEnum,
        target_id: int,
        create: bool = False,
        tag_description: str | None = None,
        audit_logger=None,
    ):
        """
        Assigns a tag to an object by tag name, optionally creating the tag
        if it does not already exist.
        """
        current_tag = self.get_by_name(db_session, tag_name)
        # Create new tag if necessary (coerce name to lowercase)
        if current_tag is None:
            if create:
                new_tag = TagCreate(name=tag_name.lower(), description=tag_description)
                new_tag_db = self.create(
                    db_session, obj_in=new_tag, audit_logger=audit_logger
                )
                current_tag = new_tag_db
            else:
                return None
        # Delegate actual tagging
        return self.assign(
            db_session,
            current_tag.id,
            target_type,
            target_id,
            audit_logger=audit_logger,
        )

    def unassign(
        self,
        db_session: Session,
        tag_id: int,
        target_type: TargetTypeEnum,
        target_id: int,
        audit_logger=None,
    ):
        """
        Unassign a tag from an object
        """
        # Make sure tag exists (use session cache)
        tag = db_session.get(Tag, tag_id)
        if tag is None:
            return None
        # Delete all links between the object and the tag
        deleted = link.delete_links(
            db_session,
            target_type,
            target_id,
            TargetTypeEnum.tag,
            tag_id,
            bidirectional=True,
            audit_logger=audit_logger,
        )
        if not deleted:
            return None
        return tag

    def unassign_by_name(
        self,
        db_session: Session,
        tag_name: str,
        target_type: TargetTypeEnum,
        target_id: int,
        audit_logger=None,
    ):
        """
        Unassign a tag from an object
        """
        current_tag = self.get_by_name(db_session, tag_name)
        if current_tag is None:
            return None
        # Delegate actual unassignment
        return self.unassign(
            db_session,
            current_tag.id,
            target_type,
            target_id,
            audit_logger=audit_logger,
        )

    def remove(self, db_session: Session, _id: int, audit_logger=None):
        link.delete_links_for_object(
            db_session,
            target_type=TargetTypeEnum.tag,
            target_id=_id,
            audit_logger=audit_logger,
        )
        return super().remove(db_session, _id=_id, audit_logger=audit_logger)


tag = CRUDTag(Tag)
