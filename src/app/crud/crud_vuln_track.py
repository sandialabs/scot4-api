from typing import get_args

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.models.vuln_track import VulnTrack
from app.schemas.vuln_track import VulnTrackCreate, VulnTrackUpdate


class CRUDVulnTrack(CRUDBase[VulnTrack, VulnTrackCreate, VulnTrackUpdate]):
    # Custom filtering for vulnerability tracks
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "subject")
        query = self._promoted_to_or_from_filter(query, filter_dict, "to")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)

    def increment_view_count(self, db_session: Session, id: int, new_transaction=True):
        vuln_track = db_session.get(VulnTrack, id)
        if vuln_track:
            if new_transaction:
                # This is okay for typical "read" use, since all we've done is
                # a single select of an object
                db_session.commit()
            # Use manual update to avoid changing the "modified" field
            db_session.execute(
                update(VulnTrack)
                .where(VulnTrack.id == id)
                .values(view_count=VulnTrack.view_count + 1, modified=VulnTrack.modified)
            )
            if new_transaction:
                # Commit as soon as possible to avoid deadlocks
                db_session.commit()
            else:
                db_session.flush()


vuln_track = CRUDVulnTrack(VulnTrack)
