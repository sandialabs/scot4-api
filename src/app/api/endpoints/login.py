from datetime import timedelta
from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.auth import auth_classes, get_authenticator
from app.core import security
from app.core.config import settings
from app.enums import AuthTypeEnum


router = APIRouter()


def login_password(
    response: Response,
    db: Session,
    form_data: OAuth2PasswordRequestForm,
    allowed_methods: list[AuthTypeEnum] | None = None,
    audit_logger: deps.AuditLogger | None = None,
):
    """
    Wrapper function to generate a password login endpoint
    """
    user = crud.user.authenticate(
        db,
        username=form_data.username,
        password=form_data.password,
        allowed_methods=allowed_methods,
        audit_logger=audit_logger,
    )
    if user is None:
        raise HTTPException(401, "Incorrect username or password")
    elif isinstance(user, str):
        raise HTTPException(400, user)
    elif not crud.user.is_active(user):
        raise HTTPException(400, "Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_roles = None
    if form_data.scopes:
        token_roles = set(form_data.scopes)
        user_roles = set([role.name for role in user.roles])
        if not token_roles.issubset(user_roles):
            raise HTTPException(403, f"User {user.username} does not possess roles: {list(token_roles - user_roles)}")
        token_roles = list(token_roles)
    access_token = security.create_access_token(
        user.username, token_roles, expires_delta=access_token_expires
    )
    secure_cookie = settings.SECURE_AUTH_COOKIE
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=secure_cookie,
        expires=int(access_token_expires.total_seconds()),
    )  # In production make sure you add secure=True
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/local", response_model=schemas.Token)
def login_local(
    response: Response,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Login only with local auth
    """
    return login_password(
        response, db, form_data, [AuthTypeEnum.local], audit_logger=audit_logger
    )


@router.post("/login/ldap", response_model=schemas.Token)
def login_ldap(
    response: Response,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Login only with ldap auth
    """
    return login_password(
        response, db, form_data, [AuthTypeEnum.ldap], audit_logger=audit_logger
    )


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    response: Response,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Get an access token for future requests
    This endpoint tries all enabled password-based auth methods
    """
    return login_password(response, db, form_data, audit_logger=audit_logger)


@router.get("/login/oauth-url")
def login_oauth_url(auth_type: Annotated[AuthTypeEnum, Query(...)], db: Session = Depends(deps.get_db)) -> Any:
    """
    Gets an oauth url for the specified auth type
    """
    # Get auth handling class
    auth_class = auth_classes.get(auth_type)
    if not auth_class:
        raise HTTPException(
            status_code=422, detail="Auth type %s not supported" % auth_type
        )
    # Get configured auth methods
    auth_methods = crud.auth_setting.get_auth_methods(db)
    auth_methods = [m for m in auth_methods if m.auth == auth_type]
    if not auth_methods:
        raise HTTPException(
            status_code=422, detail="Auth type %s not configured" % auth_type
        )
    # Use first auth method; undefined behavior if multiple configured
    # Get url from configured auth method
    authenticator = get_authenticator(auth_methods[0])
    url = authenticator.start_external_authenticate()
    return {"url": url}


def login_token(
    db: Session,
    response: Response,
    auth_type: AuthTypeEnum,
    token: dict,
    audit_logger: deps.AuditLogger | None = None
) -> Any:
    """
    Login using the specified oauth callback result
    `token` should be a dict of the server's callback response parameters
    """
    try:
        user = crud.user.authenticate(
            db, token=token, allowed_methods=[auth_type], audit_logger=audit_logger
        )
    except ValueError as e:
        raise HTTPException(401, str(e))
    if not user:
        raise HTTPException(401, "Authentication failed")
    elif not crud.user.is_active(user):
        raise HTTPException(400, "Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.username, expires_delta=access_token_expires
    )
    secure_cookie = settings.SECURE_AUTH_COOKIE
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=secure_cookie,
        expires=int(access_token_expires.total_seconds()),
    )  # In production make sure you add secure=True
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/login/aad-callback")
def login_aad_callback(
    code: Annotated[str, Query(...)],
    state: Annotated[str, Query(...)],
    response: Response,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger)
) -> Any:
    return login_token(db, response, AuthTypeEnum.aad, {"code": code, "state": state},
                       audit_logger=audit_logger)


@router.get("/login/test-token", response_model=schemas.User)
def test_token(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Test access token
    """
    return current_user


@router.get("/logout")
def logout(
    *,
    db: Session = Depends(deps.get_db),
    response: Response,
    current_user: models.User = Depends(deps.get_current_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Update your own user info
    """
    response.delete_cookie(key="access_token")
    if current_user:
        return {"msg": "Logout Successful"}
    else:
        return {"msg": "Not logged in"}
