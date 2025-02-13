from sqlalchemy import update
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.enums import PermissionEnum
from app.core.config import settings
from app.models.role import Role
from app.models.permission import Permission
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentUpdate


class CRUDIncident(CRUDBase[Incident, IncidentCreate, IncidentUpdate]):
    # Custom filtering for incidents
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "subject")
        query = self._promoted_to_or_from_filter(query, filter_dict, "from")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)

    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read
    ):
        """
        Incidents have json fields, and so need a slightly different query
        Note: admin permissions must be checked elsewhere
        """
        return db_session.query(self.model)\
            .join(Permission, (self.model.id == Permission.target_id))\
            .filter(((self.model.target_type_enum() == Permission.target_type) & (required_permission == Permission.permission)))\
            .filter(Permission.role_id.in_([role.id for role in roles] + [settings.EVERYONE_ROLE_ID]))\
            .group_by(self.model.id)  # We can't use DISTINCT with incidents

    def increment_view_count(self, db_session: Session, id: int, new_transaction=True):
        incident = db_session.get(Incident, id)
        if incident:
            if new_transaction:
                # This is okay for typical "read" use, since all we've done is
                # a single select of an object
                db_session.commit()
            # Use manual update to avoid changing the "modified" field
            db_session.execute(
                update(Incident)
                .where(Incident.id == id)
                .values(view_count=Incident.view_count + 1, modified=Incident.modified)
            )
            if new_transaction:
                # Commit as soon as possible to avoid deadlocks
                db_session.commit()
            else:
                db_session.flush()


incident = CRUDIncident(Incident)
