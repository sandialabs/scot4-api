from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user_links import UserLinks
from app.schemas.user_links import UserLinksCreate, UserLinksUpdate
from app.enums import TargetTypeEnum, UserLinkEnum


class CRUDUserLinks(CRUDBase[UserLinks, UserLinksCreate, UserLinksUpdate]):
    def get_favorite(self, db_session: Session, target_id: int, target_type: TargetTypeEnum, owner_id: int):
        return db_session.query(UserLinks)\
            .where(UserLinks.target_id == target_id)\
            .where(UserLinks.target_type == target_type)\
            .where(UserLinks.owner_id == owner_id)\
            .where(UserLinks.link_type == UserLinkEnum.favorite)\
            .first()

    def find_link(self, db_session: Session, target_type: TargetTypeEnum, target_id: int, owner_id: int, link_type: UserLinkEnum):
        return db_session.query(UserLinks)\
            .where(UserLinks.target_id == target_id)\
            .where(UserLinks.target_type == target_type)\
            .where(UserLinks.owner_id == owner_id)\
            .where(UserLinks.link_type == link_type)\
            .one_or_none()

    # going to want to also get link titles/names or whatever so that gets/creates/updates/deletes etc all have the target_id title


user_links = CRUDUserLinks(UserLinks)
