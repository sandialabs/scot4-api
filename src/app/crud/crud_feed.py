from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.core.config import settings
from app.models.feed import Feed
from app.models.role import Role
from app.models.user import User
from app.models.permission import Permission
from app.schemas.feed import FeedCreate, FeedUpdate
from app.enums import PermissionEnum


class CRUDFeed(CRUDBase[Feed, FeedCreate, FeedUpdate]):
    # Custom filtering for feeds
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "uri")

        return super().filter(query, filter_dict)

    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read
    ):
        """
        Feeds have json fields, and so need a slightly different query
        Note: admin permissions must be checked elsewhere
        """
        return db_session.query(self.model)\
            .join(Permission, (self.model.id == Permission.target_id))\
            .filter(((self.model.target_type_enum() == Permission.target_type) & (required_permission == Permission.permission)))\
            .filter(Permission.role_id.in_([role.id for role in roles] + [settings.EVERYONE_ROLE_ID]))\
            .group_by(self.model.id)  # We can't use DISTINCT with feeds


feed = CRUDFeed(Feed)
