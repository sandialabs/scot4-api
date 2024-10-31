from sqlalchemy.orm import Session

from app.auth import auth_classes
from app.crud.base import CRUDBase
from app.models.auth_settings import AuthSettings
from app.schemas.setting import (
    AuthSettingsCreate,
    AuthSettingsUpdate,
)


class CRUDSetting(CRUDBase[AuthSettings, AuthSettingsCreate, AuthSettingsUpdate]):
    def create_auth_method(
        self, db_session: Session, new_auth: AuthSettingsCreate, audit_logger=None
    ) -> AuthSettings:
        new_db_obj = AuthSettings()
        new_db_obj.auth = new_auth.auth
        # Set auth_properties to default if not explicitly set
        set_keys = new_auth.model_dump(exclude_unset=True).keys()
        if "auth_properties" not in set_keys:
            auth_class = auth_classes[new_auth.auth]
            new_db_obj.auth_properties = auth_class.default_config
        elif new_auth.auth_properties:
            new_db_obj.auth_properties = new_auth.auth_properties
        new_db_obj.auth_active = new_auth.auth_active
        if audit_logger is not None:
            audit_logger.log("create", new_db_obj)
        db_session.add(new_db_obj)
        db_session.flush()
        db_session.refresh(new_db_obj)
        return new_db_obj

    def remove_auth_method(
        self, db_session: Session, id: int, audit_logger=None
    ) -> AuthSettings:
        db_obj = super().get(db_session, id)
        if db_obj is None:
            return None
        if id == 1:
            raise ValueError("Cannot delete root auth method")
        db_session.delete(db_obj)
        db_session.flush()
        if audit_logger:
            audit_logger.log("delete", db_obj)
        return db_obj

    def update_auth_method(
        self,
        db_session: Session,
        id: int,
        obj_in: AuthSettingsUpdate,
        audit_logger=None,
    ) -> AuthSettings:
        db_obj = super().get(db_session, id)
        if db_obj:
            return self.update(
                db_session,
                db_obj=db_obj,
                obj_in=obj_in.model_dump(exclude_unset=True),
                audit_logger=audit_logger,
            )
        else:
            return None

    def get_auth_methods(self, db_session: Session) -> list[AuthSettings]:
        return db_session.query(self.model).order_by(AuthSettings.id).all()

    def get_auth_help(self) -> dict:
        pretty_names = {
            auth.value: auth_classes[auth].config_name_pretty for auth in auth_classes
        }
        config_help = {
            auth.value: auth_classes[auth].config_help for auth in auth_classes
        }
        return {"config_name_pretty": pretty_names, "config_help": config_help}


auth_setting = CRUDSetting(AuthSettings)
