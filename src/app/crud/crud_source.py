from datetime import datetime
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.crud.crud_appearance import appearance
from app.crud.crud_link import link
from app.enums import TargetTypeEnum, PermissionEnum
from app.models.link import Link
from app.models.source import Source
from app.models.role import Role
from app.schemas.appearance import AppearanceCreate
from app.schemas.source import SourceCreate, SourceUpdate


class CRUDSource(CRUDBase[Source, SourceCreate, SourceUpdate]):
    def get_by_name(self, db_session: Session, source_name: str):
        query = db_session.query(Source).filter(Source.name == source_name.lower())
        query = query.order_by(Source.id)
        return query.first()   # Return source with lowest id if multiple exist

    # All sources are inherently queryable by anyone

    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read,
    ):
        return db_session.query(self.model)

    # Custom filtering for sources
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "name")
        query = self._str_filter(query, filter_dict, "description")

        return super().filter(query, filter_dict)

    def assign(
        self,
        db_session: Session,
        source_id: int,
        target_type: TargetTypeEnum,
        target_id: int,
        audit_logger=None,
    ):
        """
        Assigns a source to an object by source id; the existence of the object
        is NOT checked.
        """
        # Make sure source exists (use session cache)
        source = db_session.get(Source, source_id)
        if source is None:
            return None
        # Ensure that the object is not already tagged with this tag
        existing = (
            db_session.query(Link)
            .filter(
                (Link.v0_type == target_type)
                & (Link.v0_id == target_id)
                & (Link.v1_type == TargetTypeEnum.source)
                & (Link.v1_id == source_id)
            )
            .first()
        )
        if not existing:
            # Do the actual assignment
            new_link = {
                "v0_type": target_type,
                "v0_id": target_id,
                "v1_type": TargetTypeEnum.source,
                "v1_id": source_id,
                "weight": 1,
                "context": "sourced from",
            }
            link.create(db_session, obj_in=new_link, audit_logger=audit_logger)
            # Add to appearances table
            new_appearance = AppearanceCreate(
                when_date=datetime.utcnow(),
                target_type=target_type,
                target_id=target_id,
                value_type=TargetTypeEnum.source.value,
                value_id=source_id,
                value_str=source.name,
            )
            appearance.create(
                db_session, obj_in=new_appearance, audit_logger=audit_logger
            )
        return source

    def assign_by_name(
        self,
        db_session: Session,
        source_name: str,
        target_type: TargetTypeEnum,
        target_id: int,
        create: bool = False,
        source_description: str | None = None,
        audit_logger=None,
    ):
        """
        Assigns a source to an object by source name, optionally creating the
        source if it does not already exist.
        """

        current_source = self.get_by_name(db_session, source_name)
        # Create new source if necessary
        if current_source is None:
            if create:
                new_source = SourceCreate(
                    name=source_name.lower(), description=source_description
                )
                current_source = self.create(
                    db_session, obj_in=new_source, audit_logger=audit_logger
                )
            else:
                return None
        # Delegate actual assignment
        return self.assign(
            db_session,
            current_source.id,
            target_type,
            target_id,
            audit_logger=audit_logger,
        )

    def unassign(
        self,
        db_session: Session,
        source_id: int,
        target_type: TargetTypeEnum,
        target_id: int,
        audit_logger=None,
    ):
        """
        Unassign a source from an object
        """
        # Make sure source exists (use session cache)
        source = db_session.get(Source, source_id)
        if source is None:
            return None
        # Delete all links between the object and the source
        deleted = link.delete_links(
            db_session,
            target_type,
            target_id,
            TargetTypeEnum.source,
            source_id,
            bidirectional=True,
            audit_logger=audit_logger,
        )
        if not deleted:
            return None
        return source

    def unassign_by_name(
        self,
        db_session: Session,
        source_name: str,
        target_type: TargetTypeEnum,
        target_id: int,
        audit_logger=None,
    ):
        """
        Unassign a source from an object
        """
        current_source = self.get_by_name(db_session, source_name)
        if current_source is None:
            return None
        # Delegate actual unassignment
        return self.unassign(
            db_session,
            current_source.id,
            target_type,
            target_id,
            audit_logger=audit_logger,
        )

    def remove(self, db_session: Session, _id: int, audit_logger=None):
        link.delete_links_for_object(
            db_session,
            target_type=TargetTypeEnum.source,
            target_id=_id,
            audit_logger=audit_logger,
        )
        return super().remove(db_session, _id=_id, audit_logger=audit_logger)


source = CRUDSource(Source)
