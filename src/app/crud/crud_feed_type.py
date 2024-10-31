from app.crud.base import CRUDBase
from app.models.feed_type import FeedType
from app.schemas.feed_type import FeedTypeCreate, FeedTypeUpdate


class CRUDFeedType(CRUDBase[FeedType, FeedTypeCreate, FeedTypeUpdate]):
    pass


feed_type = CRUDFeedType(FeedType)
