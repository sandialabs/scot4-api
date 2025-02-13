from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.enums import TargetTypeEnum
from app.models.popularity import Popularity
from app.schemas.popularity import PopularityCreate, PopularityUpdate


class CRUDPopularity(CRUDBase[Popularity, PopularityCreate, PopularityUpdate]):
    def get_user_metric(self, db_session: Session, target_type: TargetTypeEnum, target_id: int, owner_id: int) -> Popularity:
        return (
            db_session.query(Popularity)
            .where(Popularity.target_type == target_type)
            .where(Popularity.target_id == target_id)
            .where(Popularity.owner_id == owner_id)
            .first()
        )


popularity = CRUDPopularity(Popularity)
