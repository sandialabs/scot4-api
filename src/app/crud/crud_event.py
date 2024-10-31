from sqlalchemy import update
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.models.event import Event
from app.schemas.event import EventCreate, EventUpdate


class CRUDEvent(CRUDBase[Event, EventCreate, EventUpdate]):
    # Custom filtering for events
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "subject")
        query = self._promoted_to_or_from_filter(query, filter_dict, "to")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)

    def increment_view_count(self, db_session: Session, id: int, new_transaction=True):
        event = db_session.get(Event, id)
        if event:
            if new_transaction:
                # This is okay for typical "read" use, since all we've done is
                # a single select of an object
                db_session.commit()
            # Use manual update to avoid changing the "modified" field
            db_session.execute(
                update(Event)
                .where(Event.id == id)
                .values(view_count=Event.view_count + 1, modified=Event.modified)
            )
            if new_transaction:
                # Commit as soon as possible to avoid deadlocks
                db_session.commit()
            else:
                db_session.flush()


event = CRUDEvent(Event)
