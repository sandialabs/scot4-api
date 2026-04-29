from sqlalchemy.orm import Session

from app import models, crud
from app.enums import TargetTypeEnum
from app.models import ThreatModelItem, Role, Signature, Link
from app.schemas import ThreatModelItemCreate, ThreatModelItemUpdate
from app.crud.base import CRUDBase


class CRUDThreatModelItem(CRUDBase[models.ThreatModelItem, ThreatModelItemCreate, ThreatModelItemUpdate]):
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "threat_model_id")
        query = self._str_filter(query, filter_dict, "title")
        query = self._str_filter(query, filter_dict, "description")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)

    def get_signatures_for(
        self,
        db_session: Session,
        id: int,
        roles: list[Role] = None
    ):
        threat_model_item = self.get(db_session, id)
        if not threat_model_item:
            return None
        if roles is None or crud.permission.roles_have_admin(db_session, roles):
            query = db_session.query(Signature)
        else:
            query = crud.signature.query_objects_with_roles(db_session, roles)
        query = query.join(Link, (Link.v0_id == Signature.id)
                           & (Link.v0_type == TargetTypeEnum.signature)
                           & (Link.v1_id == id)
                           & (Link.v1_type == TargetTypeEnum.threat_model_item))
        return query.all()


threat_model_item = CRUDThreatModelItem(ThreatModelItem)
