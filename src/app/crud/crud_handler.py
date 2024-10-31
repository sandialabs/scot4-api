from datetime import datetime
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.handler import Handler
from app.schemas.handler import HandlerCreate, HandlerUpdate


class CRUDHandler(CRUDBase[Handler, HandlerCreate, HandlerUpdate]):
    def get_handlers_in_date_range(
        self,
        db_session: Session,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ):
        # Get all entries with start or end in the range (or an entry that
        # encompasses the range)
        query = db_session.query(Handler).filter(
            ((start_date < Handler.start_date) & (end_date > Handler.start_date))
            | ((start_date < Handler.end_date) & (end_date > Handler.end_date))
            | ((start_date > Handler.start_date) & (end_date < Handler.end_date))
        )
        count = query.count()
        if skip and skip > 0:
            query = query.offset(skip)
        query = query.limit(limit)

        # query = query.offset(skip).limit(limit)
        return query.all(), count


handler = CRUDHandler(Handler)
