from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.remote_flair import RemoteFlair
from app.schemas.remote_flair import RemoteFlairCreate, RemoteFlairUpdate


class CRUDRemoteFlair(CRUDBase[RemoteFlair, RemoteFlairCreate, RemoteFlairUpdate]):
    def get_md5(self, db_session: Session, md5: str) -> RemoteFlair:
        return db_session.query(RemoteFlair).filter(RemoteFlair.md5 == md5).first()


remote_flair = CRUDRemoteFlair(RemoteFlair)
