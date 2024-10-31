from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.apikey import ApiKey
from app.schemas.apikey import ApiKey as ApiKeySchema


class CRUDApiKey(CRUDBase[ApiKey, ApiKeySchema, ApiKeySchema]):
    def get(self, db_session: Session, key: str) -> ApiKey | None:
        CRUDBase.publish("get", key)
        return db_session.query(self.model).filter(self.model.key == key).first()

    def remove(self, db_session: Session, *, key: str) -> ApiKey:
        obj = self.get(db_session, key)
        db_session.delete(obj)
        db_session.flush()
        return obj


apikey = CRUDApiKey(ApiKey)
