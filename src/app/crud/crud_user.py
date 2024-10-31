from datetime import datetime
from typing import Any, Union
from sqlalchemy.orm import Session

from app.auth import get_authenticator
from app.core.config import settings
from app.core.security import get_password_hash
from app.crud.base import CRUDBase
from app.crud.crud_role import role
from app.crud.crud_auth_setting import auth_setting
from app.enums import AuthTypeEnum
from app.models import Audit, User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    @staticmethod
    def get_by_username(
        db_session: Session, *, username: str, audit_logger=None
    ) -> User | None:
        query = db_session.query(User).filter(User.username == username)
        result = query.first()
        if audit_logger is not None:
            audit_logger.log("read", result, log_thing=False)
        return result

    def bulk_get_by_usernames(
        self, db_session: Session, username_list: list[str], audit_logger=None
    ) -> list[User | None]:
        """
        Get many users by username, who may or may not exist
        Returns a list of user objects in the same order, or None if the user
        with that username did not exist
        """
        query = db_session.query(User).filter(User.username.in_(username_list))
        user_list = query.all()
        user_dict = {u.username: u for u in user_list}
        return [
            user_dict[name] if name in user_dict else None for name in username_list
        ]

    #
    # async def get_user(username: str, db: Session = Depends(get_db)):
    #     user = db.query(User).filter(User.username == username).first()
    #     if not user:
    #         raise HTTPException(status_code=404, detail="User not found")
    #     return user

    def create(
        self, db_session: Session, *, obj_in: UserCreate, audit_logger=None
    ) -> User:
        pw_hash = None
        if obj_in.password is not None:
            pw_hash = get_password_hash(obj_in.password)
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            is_active=obj_in.is_active,
            pw_hash=pw_hash,
            fullname=obj_in.fullname,
            is_superuser=obj_in.is_superuser,
        )
        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)
        if audit_logger is not None:
            audit_logger.log("create", db_obj)
        # Add roles (if any; will only add roles that already exist)
        if obj_in.roles:
            role.ensure_roles_on_user(
                db_session,
                db_obj,
                obj_in.roles,
                create=False,
                audit_logger=audit_logger,
            )
        return db_obj

    def update(
        self,
        db_session: Session,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, dict[str, Any]],
        audit_logger=None
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["pw_hash"] = hashed_password
        return super().update(
            db_session, db_obj=db_obj, obj_in=update_data, audit_logger=audit_logger
        )

    def authenticate(
        self,
        db_session: Session,
        *,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        allowed_methods: list[AuthTypeEnum] = None,
        audit_logger=None
    ) -> User | None:
        result = None
        # Try password auth first
        if username is not None and password is not None:
            result = self.authenticate_password(
                db_session,
                username,
                password,
                allowed_methods,
                audit_logger=audit_logger,
            )
        # Try token if provided and not already authenticated
        if not result and token is not None:
            result = self.authenticate_token(
                db_session, token, allowed_methods, audit_logger=audit_logger
            )
        # Store login time if successful
        if isinstance(result, User):
            result.last_login = datetime.utcnow()
            self.update_last_activity(db_session, result)
        return result

    def authenticate_password(
        self,
        db_session: Session,
        username: str,
        password: str,
        allowed_methods: list[AuthTypeEnum] = None,
        audit_logger=None,
    ) -> User | None:
        auth_methods = auth_setting.get_auth_methods(db_session)
        user = self.get_by_username(db_session, username=username)
        # Check if this user has too many failed password attempts
        if user and user.failed_attempts >= settings.MAX_FAILED_PASSWORD_ATTEMPTS:
            return (
                "Max password retry attempts exceeded, contact your "
                "administrator for assistance"
            )
        if allowed_methods is not None:
            auth_methods = [m for m in auth_methods if m.auth in allowed_methods]
        for method in auth_methods:
            if not method.auth_active:
                continue
            try:
                authorizer = get_authenticator(method)
                if authorizer:
                    auth_result = authorizer.authenticate_password(
                        username, password, user
                    )
                    if auth_result and not user:
                        # Need to create new user
                        user = self.create(
                            db_session, obj_in=auth_result, audit_logger=audit_logger
                        )
                    if auth_result:
                        # Log successful authentication
                        if audit_logger is not None:
                            action_string = "login_password_" + method.auth.value
                            audit_logger.log(
                                action_string, None, thing_type=User, thing_pk=username
                            )
                        # Add any missing roles to the user
                        autocreate_groups = (
                            not hasattr(authorizer, "group_autocreate")
                            or authorizer.group_autocreate
                        )
                        role.ensure_roles_on_user(
                            db_session,
                            user,
                            auth_result.roles,
                            auth_method=method,
                            create=autocreate_groups,
                            audit_logger=audit_logger,
                        )
                        # Reset failed password count to 0
                        user.failed_attempts = 0
                        # Auth successful
                        return user
            except NotImplementedError:
                # This auth method doesn't support passwords
                continue
        # All auth methods failed
        if audit_logger is not None:
            audit_logger.log(
                "login_password_failed", None, thing_type=User, thing_pk=username
            )
        # Manually update failed password count
        db_session.query(User).filter(User.username == username).update(
            {"failed_attempts": User.failed_attempts + 1}
        )
        return None

    def authenticate_token(
        self,
        db_session: Session,
        token: dict,
        allowed_methods: list[AuthTypeEnum] = None,
        audit_logger=None,
    ) -> User | None:
        auth_methods = auth_setting.get_auth_methods(db_session)
        user = None
        if allowed_methods is not None:
            auth_methods = [m for m in auth_methods if m.auth in allowed_methods]
        for method in auth_methods:
            if not method.auth_active:
                continue
            try:
                authorizer = get_authenticator(method)
                if authorizer:
                    auth_result = authorizer.authenticate_token(token, user)
                    # Need to look for user after auth_result
                    if isinstance(auth_result, UserCreate):
                        user = self.get_by_username(
                            db_session, username=auth_result.username
                        )
                    if auth_result and not user:
                        # Need to create new user
                        user = self.create(db_session, obj_in=auth_result)
                    if auth_result:
                        # Log successful authentication
                        if audit_logger is not None:
                            action_string = "login_token_" + method.auth.value
                            audit_logger.log(action_string, None,
                                             thing_type=User, thing_pk=user.username)
                        # Add any missing roles to the user
                        autocreate_groups = (
                            not hasattr(authorizer, "group_autocreate")
                            or authorizer.group_autocreate
                        )
                        role.ensure_roles_on_user(
                            db_session,
                            user,
                            auth_result.roles,
                            auth_method=method,
                            create=autocreate_groups,
                            audit_logger=audit_logger,
                        )
                        # Auth successful
                        return user
            except NotImplementedError:
                # This auth method doesn't support tokens
                continue
        # All auth methods failed
        if audit_logger is not None:
            audit_logger.log(
                "login_token_failed", None, thing_type=User, thing_pk="_UNKNOWN_USER"
            )
        return None

    def update_last_activity(self, db_session: Session, user: User):
        user.last_activity = datetime.utcnow()
        db_session.add(user)
        db_session.flush()

    def reset_failed_attempts(self, db_session: Session, username: str):
        """
        Resets the user's count of failed login attempts
        """
        user = db_session.query(User).filter(User.username == username).first()
        if not user:
            return None
        user.failed_attempts = 0
        db_session.add(user)
        return user

    def undelete(
        self,
        db_session: Session,
        target_id: int | None = None,
        username: str | None = None,
        existing_data=None,
        keep_ids: bool = True,
        by_user: str | None = None,
        audit_logger=None,
    ):
        """
        Additional undelete functionality to reassign roles
        """
        # Get user deletion from logs
        if existing_data is None:
            if target_id is None and username is None:
                raise ValueError("Must specify target id or username to restore")
            pk_to_search = username if username is not None else target_id
            query = db_session.query(Audit).filter(
                (Audit.what == "delete")
                & (Audit.thing_type == "user")
                & (Audit.thing_id == pk_to_search)
            )
            if by_user is not None:
                query.filter(Audit.username == by_user)
            audit = query.order_by(Audit.when_date.desc()).first()
            if not audit:
                raise ValueError("Target deleted object not found")
            object_data = audit.audit_data
        else:
            object_data = existing_data
        restored_user = super().undelete(
            db_session,
            existing_data=object_data,
            keep_ids=keep_ids,
            audit_logger=audit_logger,
        )
        # Reassign roles
        if "roles" in object_data:
            role_names = [r.name for r in object_data["roles"]]
            role.ensure_roles_on_user(
                db_session,
                user=restored_user,
                role_names=role_names,
                create=False,
                audit_logger=audit_logger,
            )
        db_session.refresh(restored_user)
        return restored_user

    @staticmethod
    def is_active(user: User) -> bool:
        return user and user.is_active

    @staticmethod
    def is_superuser(user: User) -> bool:
        return user and user.is_superuser


user = CRUDUser(User)
