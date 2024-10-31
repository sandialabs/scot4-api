from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.entity_class import EntityClass
from app.schemas.entity_class import EntityClassCreate, EntityClassUpdate


class CRUDEntityClass(CRUDBase[EntityClass, EntityClassCreate, EntityClassUpdate]):
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "description")

        return super().filter(query, filter_dict)

    def get_by_name(self, db_session: Session, name: str):
        return db_session.query(EntityClass).filter(EntityClass.name == name).one_or_none()


entity_class = CRUDEntityClass(EntityClass)
