from typing import Any, Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic.json_schema import SkipJsonSchema
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email, create_schema_details

router = APIRouter()

# https://www.python-ldap.org/en/python-ldap-3.3.0/reference/ldap.html#example
# https://github.com/AzureAD/microsoft-authentication-library-for-python


@router.get(
    "/",
    response_model=schemas.ListResponse[schemas.User],
    dependencies=[Depends(deps.admin_only)],
    summary="Get users"
)
def read_users(
    db: Session = Depends(deps.get_db),
    skip: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = -1,
    sort: Annotated[str | SkipJsonSchema[None], Query(...)] = None,
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Get all users (admin only)
    """
    users, count = crud.user.query_with_filters(db, None, None, sort, skip, limit, audit_logger)
    return {"result": users, "resultCount": len(users), "totalCount": count}


@router.get(
    "/usernames",
    response_model=schemas.ListResponse[str],
    dependencies=[Depends(deps.get_current_active_user)],
    summary="Get usernames"
)
def read_usernames(
    db: Session = Depends(deps.get_db),
    skip: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = -1,
) -> Any:
    """
    Read usernames of users (admin not required)
    """
    users, count = crud.user.query_with_filters(db, None, None, "username", skip, limit)
    usernames = [u.username for u in users]
    return {"result": usernames, "resultCount": len(usernames), "totalCount": count}


@router.get(
    "/activity",
    response_model=dict[str, datetime],
    dependencies=[Depends(deps.get_current_active_user)],
    summary="Get recent activity",
    responses={
        200: {
            "content": {"application/json": {"example": {"user1": "2025-01-01T08:00:00Z", "user2": "2025-01-01T18:00:00Z"}}}
        }
    }
)
def read_activity(
    db: Session = Depends(deps.get_db),
    skip: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = -1,
) -> Any:
    """
    Read activity of users (admin not required)
    Limited to last 30 minutes of activity
    """
    users, _ = crud.user.query_with_filters(
        db,
        None,
        {
            "last_activity": (datetime.utcnow() - timedelta(minutes=30), datetime.utcnow() + timedelta(seconds=30))
        },
        "last_activity",
        skip,
        limit,
    )
    resultDict = {u.username: u.last_activity.replace(tzinfo=timezone.utc) for u in users}
    return resultDict


description, examples = create_schema_details(schemas.UserCreate, "Create a new user (admin only)")


@router.post("/", response_model=schemas.User, dependencies=[Depends(deps.admin_only)], description=description)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: Annotated[schemas.UserCreate, Body(..., openapi_examples=examples)],
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Create a new user (admin only)
    """
    user = crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(400, "The user with this username already exists in the system.")
    user = crud.user.create(db, obj_in=user_in, audit_logger=audit_logger)
    if settings.EMAILS_ENABLED and user_in.email:
        send_new_account_email(user_in.email, user_in.email, user_in.password)
    return user


@router.put("/me", response_model=schemas.User, summary="Update own user")
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    password: Annotated[str | None, Body(...)] = None,
    fullname: Annotated[str | None, Body(...)] = None,
    email: Annotated[EmailStr | None, Body(...)] = None,
    preferences: Annotated[dict | None, Body(...)] = None,
    current_user: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Update your own user info
    """
    user_in = schemas.UserUpdate()
    if password is not None:
        user_in.password = password
    if fullname is not None:
        user_in.fullname = fullname
    if email is not None:
        user_in.email = email
    if preferences is not None:
        user_in.preferences = preferences
    return crud.user.update(db, db_obj=current_user, obj_in=user_in, audit_logger=audit_logger)


@router.get("/whoami", response_model=schemas.User, summary="Get own user")
def read_user_who_am_i(
    _: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the current authenticated user
    """
    return current_user


@router.post("/open", response_model=schemas.User, summary="Sign up a user")
def create_user_open(
    *,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    username: Annotated[str, Body(...)],
    password: Annotated[str, Body(...)],
    email: Annotated[EmailStr, Body(...)],
    fullname: Annotated[str, Body(...)] = "",
) -> Any:
    """
    Create new user without the need to be logged in
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(403, "User registration disabled")
    user = crud.user.get_by_email(db, email=email)
    if user:
        raise HTTPException(400, "The user with this email already exists in the system")

    return crud.user.create(db, obj_in=schemas.UserCreate(password=password, email=email, fullname=fullname), audit_logger=audit_logger)


@router.get("/{id_or_username}", response_model=schemas.User, summary="Get user info")
def read_user(
    id_or_username: Annotated[int | str, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Get a specific user by id or username
    """
    try:
        user = crud.user.get(db_session=db, _id=int(id_or_username), audit_logger=audit_logger)
    except ValueError:
        user = crud.user.get_by_username(db_session=db, username=id_or_username, audit_logger=audit_logger)

    if user is None:
        raise HTTPException(404, f"User {id} not found")

    if user == current_user:
        return user

    if not crud.user.is_superuser(current_user):
        raise HTTPException(400, "The user doesn't have enough privileges")

    return user


description, examples = create_schema_details(schemas.UserUpdate, "Update a user (admin only)")


@router.put("/{id}", response_model=schemas.User, dependencies=[Depends(deps.admin_only)], description=description, summary="Update a user")
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    user_in: Annotated[schemas.UserUpdate, Body(..., openapi_examples=examples)],
    _: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Update a user (admin only)
    """
    user = crud.user.get(db, id)
    if not user:
        raise HTTPException(404, "The user with this id does not exist in the system")

    return crud.user.update(db, db_obj=user, obj_in=user_in, audit_logger=audit_logger)


@router.delete(
    "/{id}",
    response_model=schemas.User,
    dependencies=[Depends(deps.admin_only)],
    summary="Delete user"
)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Delete a user
    """
    user = crud.user.get(db, id)
    if not user:
        raise HTTPException(404, "The user with this id does not exist in the system")

    return crud.user.remove(db, _id=id, audit_logger=audit_logger)


@router.post(
    "/{username}/reset-failed-attempts",
    response_model=schemas.Msg,
    dependencies=[Depends(deps.admin_only)],
    summary="Reset failed password attempts"
)
def reset_failed_attempts(
    username: Annotated[str, Path(...)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Resets the given user's number of failed password attempts to zero
    """
    user = crud.user.reset_failed_attempts(db, username)
    if user is None:
        raise HTTPException(404, "The user with this id does not exist in the system")
    return schemas.Msg(msg="Password attempts for user %s reset successfully" % username)
