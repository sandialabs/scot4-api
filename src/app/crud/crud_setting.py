from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.settings import Settings
from app.schemas.setting import (
    SettingsCreate,
    SettingsUpdate,
)


class CRUDSetting(CRUDBase[Settings, SettingsCreate, SettingsUpdate]):
    @staticmethod
    def update(
        db_session: Session,
        *,
        obj_in: SettingsUpdate,
        db_obj: Settings = None,
        audit_logger=None
    ) -> Settings:
        # If a settings object isn't provided, assume we're updating the
        # root settings
        if db_obj is None:
            db_obj = setting.get(db_session)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            if field in SettingsUpdate.model_json_schema()["properties"]:
                setattr(db_obj, field, update_data[field])
        if audit_logger is not None:
            audit_logger.log("update", update_data)
        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)
        return db_obj

    def get(self, db_session: Session, audit_logger=None, **kwargs) -> Settings:
        result = db_session.query(self.model).order_by(self.model.id).first()
        if audit_logger is not None:
            audit_logger.log("read", result, log_thing=False)
        return result


setting = CRUDSetting(Settings)
