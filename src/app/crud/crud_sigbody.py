from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.models.sigbody import Sigbody
from app.schemas.sigbody import SigbodyCreate, SigbodyUpdate


class CRUDSigbody(CRUDBase[Sigbody, SigbodyCreate, SigbodyUpdate]):
    # Custom filtering for products
    def filter(self, query, filter_dict):
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)

    def get_sigbodies_for_signature(self, db_session: Session, signature_id: int):
        return (
            db_session.query(Sigbody).filter(Sigbody.signature_id == signature_id).all()
        )


sigbody = CRUDSigbody(Sigbody)
