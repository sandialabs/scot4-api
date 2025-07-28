import json
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Query, Path
from fastapi.encoders import jsonable_encoder
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.crud import permission
from app.db.base_class import Base
from app.enums import PermissionEnum, TargetTypeEnum
from app.utils import OAuth2PasswordBearerWithCookie

reusable_oauth2 = OAuth2PasswordBearerWithCookie(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token", auto_error=False
)


def get_db(request: Request):
    if hasattr(request.state, "db"):
        return request.state.db
    else:
        raise HTTPException(status=500, detail="Could not get database session")


# Changes an api token to a JWT token if present
def api_token_mixin(request: Request, db: Session = Depends(get_db)):
    MIXIN_TOKEN_EXPIRES = timedelta(seconds=5)
    authorization_header = request.headers.get("authorization")
    token = None
    if authorization_header and authorization_header.startswith("apikey"):
        key = "".join(authorization_header.split()[1:])
        api_key = crud.apikey.get(db, key)
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        if not api_key.active:
            raise HTTPException(status_code=401, detail="This API key is not active")
        token_roles = None
        if api_key.roles:
            token_roles = [role.name for role in api_key.roles]
        jwt_token = security.create_access_token(
            api_key.owner, token_roles, expires_delta=MIXIN_TOKEN_EXPIRES
        )
        # Remove old authorization header and inject new one
        request.headers.__dict__["_list"].remove(
            (b"authorization", authorization_header.encode("utf-8"))
        )
        request.headers.__dict__["_list"].append(
            (b"authorization", b"Bearer " + jwt_token.encode("utf-8"))
        )
        token = api_key.key
        request.state.apikey = api_key
    else:
        request.state.apikey = None
    return token


def get_token_data(
    mixin: str = Depends(api_token_mixin),
    token: str = Depends(reusable_oauth2),
) -> schemas.TokenPayload:
    try:
        if token:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
            )
            token_data = schemas.TokenPayload(**payload)
        else:
            token_data = None
    except (jwt.JWTError, ValidationError):
        # Token validation failed; continue as if there's no token
        token_data = None
    return token_data


def get_token_data_no_apikey(
    token: str = Depends(reusable_oauth2),
) -> schemas.TokenPayload:
    try:
        if token:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
            )
            token_data = schemas.TokenPayload(**payload)
        else:
            token_data = None
    except (jwt.JWTError, ValidationError):
        # Token validation failed; continue as if there's no token
        token_data = None
    return token_data


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token_data: schemas.TokenPayload = Depends(get_token_data),
) -> models.User:
    user = None
    if token_data:
        user = crud.user.get_by_username(db, username=token_data.u)
    return user  # Can be None


def get_current_active_user(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
) -> models.User:
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    crud.user.update_last_activity(db, current_user)
    # add user id to the session for some queries
    db.info["user_id"] = current_user.id
    db.commit()  # Done here to prevent race conditions
    return current_user


def get_current_roles(
    token_data: schemas.TokenPayload = Depends(get_token_data),
    current_user: models.User = Depends(get_current_active_user),
) -> list[models.Role]:
    if token_data.token_roles:
        return [
            role for role in current_user.roles if role.name in token_data.token_roles
        ]
    else:
        return current_user.roles


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


# Class that logs audit entries with a specific context (the fields that are
# static per session)
AUDIT_DATA_VERSION = "0.1"


class AuditLogger:
    def __init__(self, username, source_ip, user_agent, db_session=None):
        self.username = username
        self.source_ip = source_ip
        self.user_agent = user_agent
        self.db_session = db_session
        self.audit_data_version = AUDIT_DATA_VERSION
        self.audit_objects = []

    def log(self, action, thing, thing_type=None, thing_pk=None, log_thing=True,
            thing_subtype=None):
        """
        Logs an instance of <action> on <thing>
        <thing> is typically a database model
        """
        if not log_thing:
            data = None
        elif isinstance(thing, Base):
            # Fields we don't want in the audit logs due to prettiness problems
            # schema_column (Alert) - contains references to parent
            #       alert/schema objects
            # entity_type (Entity) - contains references to all entities for
            #       the entity type
            # tag_type (Tag) - contains references to all tags for the type
            # permissions (Role) - contains all permissions the role is a
            #       part of (only for cascade purposes)
            excluded_fields = ["schema_column", "entity_type", "tag_type",
                               "permissions"]
            data = json.dumps(
                jsonable_encoder(thing.as_dict(exclude_keys=excluded_fields))
            )
        elif thing is not None:
            data = json.dumps(jsonable_encoder(thing))
        else:
            data = None
        # Get a descriptive name for what this thing is
        if isinstance(thing, Base) and thing_type is None:
            thing_type = thing.target_type_enum()
            if thing_type == TargetTypeEnum.none:
                thing_type = type(thing).__name__.lower()
        elif thing_type is None:
            thing_type = TargetTypeEnum.none
        elif not isinstance(thing_type, (str, TargetTypeEnum)):
            thing_type = thing_type.__name__.lower()
        if isinstance(thing_type, TargetTypeEnum):
            thing_type = str(thing_type.value)
        # If the subtype (rare) is a TargetTypeEnum, convert to a string
        if isinstance(thing_subtype, TargetTypeEnum):
            thing_subtype = str(thing_subtype.value)
        # Get a primary key that identifies the thing (if any)
        pk = thing_pk
        if pk is None and hasattr(thing, "id"):
            pk = thing.id
        elif pk is None and hasattr(thing, "username"):
            pk = thing.username
        # "what" string is just the action
        what_string = action
        # Try to correct for when there's no username to log (e.g. login)
        if self.username is None and isinstance(pk, str):
            self.username = pk
        # Find the target id
        thing_id = None
        if pk and isinstance(pk, int):
            thing_id = pk
        elif hasattr(thing, "id"):
            thing_id = thing.id
        # Create the audit entry
        audit = schemas.AuditCreate(
            when_date=datetime.utcnow(),
            username=self.username,
            what=what_string,
            thing_type=thing_type,
            thing_subtype=thing_subtype,
            thing_id=thing_id,
            src_ip=self.source_ip,
            user_agent=self.user_agent,
            audit_data_ver=self.audit_data_version,
            audit_data=data,
        )
        self.audit_objects.append(audit)

    def save_audits(self, db: Session | None = None):
        if db is None:
            db = self.db_session
        crud.audit.create_batch(db, self.audit_objects)


# Dependency to get the audit logger of the current request
def get_audit_logger(
    request: Request,
    db_session: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> AuditLogger:
    username = current_user.username if current_user else None
    ipaddr = request.client.host
    # The end ip address is NUM_TRUSTED_PROXIES from the end of x-forwarded-for
    if settings.NUM_TRUSTED_PROXIES and request.headers.get("x-forwarded-for"):
        forwarded = request.headers.get("x-forwarded-for").split(", ")
        if len(forwarded) >= settings.NUM_TRUSTED_PROXIES:
            ipaddr = forwarded[-settings.NUM_TRUSTED_PROXIES]
    logger = AuditLogger(
        username,
        ipaddr,
        request.headers.get("user-agent", None),
        db_session=db_session,
    )
    request.state.audit_logger = logger
    return logger


# Dependency class to check a *specific* permission (like user.read)
# Always lets an admin through unless explicitly denied
class PermissionCheck:
    # Types that are always globally accessible by any logged-in user
    # Includes None for compatibility
    type_allow_whitelist = [TargetTypeEnum.entity, TargetTypeEnum.tag,
                            TargetTypeEnum.source, TargetTypeEnum.entity_class,
                            TargetTypeEnum.pivot, TargetTypeEnum.entity_type,
                            TargetTypeEnum.special_metric, TargetTypeEnum.none,
                            None]

    def __init__(self, target_type, permission, allow_admin=True):
        self.target_type = target_type
        self.permission = permission
        self.allow_admin = allow_admin

    def __call__(
        self,
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_active_user),
        roles: list[models.Role] = Depends(get_current_roles),
    ):
        if not self.check_permissions(db, roles, user):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource, or "
                "it does not exist.",
            )
        return True

    # Check permissions relationship
    def check_permissions(self, db, roles, user, target_id=None):
        permissions = permission.get_permissions_from_roles(
            db, roles, self.target_type, target_id
        )
        return (
            self.permission in permissions
            or (PermissionEnum.admin in permissions and self.allow_admin)
            or crud.user.is_superuser(user)
            or self.target_type in self.type_allow_whitelist
        )


# Importable permission to only allow admin access
admin_only = PermissionCheck(TargetTypeEnum.admin, PermissionEnum.admin)


# Same as above, except the dependency call takes an integer id parameter
# Permissions are only checked on the object with that id
class PermissionCheckId(PermissionCheck):
    def __call__(
        self,
        id: Annotated[int, Path(...)],
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_active_user),
        roles: list[models.Role] = Depends(get_current_roles),
    ):
        if not self.check_permissions(db, roles, user, id):
            raise HTTPException(403, "You do not have permission to access this resource, or it does not exist")
        return True


# Same as above, except for many objects
class PermissionCheckIds(PermissionCheck):
    def __call__(
        self,
        ids: Annotated[list[int], Query(...)],
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_active_user),
        roles: list[models.Role] = Depends(get_current_roles),
    ):
        for id in ids:
            if not self.check_permissions(db, roles, user, id):
                raise HTTPException(403, "You do not have permission to access this resource, or it does not exist")
        return True
