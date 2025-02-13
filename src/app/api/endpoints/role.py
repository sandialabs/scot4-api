from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.utils import create_schema_details

router = APIRouter()


description, examples = create_schema_details(schemas.RoleUpdate)


@router.put(
    "/{id}", response_model=schemas.Role, dependencies=[Depends(deps.admin_only)], description=description
)
def update_role(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    role: Annotated[schemas.RoleUpdate, Body(..., openapi_examples=examples)],
    _: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Update a role
    """
    _role = crud.role.get(db, id)
    if not _role:
        raise HTTPException(404, "Role not found")

    return crud.role.update(db, db_obj=_role, obj_in=role, audit_logger=audit_logger)


description, examples = create_schema_details(schemas.RoleCreate)


@router.post("/", response_model=schemas.Role, dependencies=[Depends(deps.admin_only)], description=description)
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role: Annotated[schemas.RoleCreate, Body(..., openapi_examples=examples)],
    _: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Create new role.
    """
    return crud.role.create(db, obj_in=role, audit_logger=audit_logger)


@router.get("/{id}", response_model=schemas.Role, dependencies=[Depends(deps.admin_only)])
def read_role(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Get role by ID.
    """
    _role = crud.role.get(db, id, audit_logger)
    if not _role:
        raise HTTPException(404, "Role not found")

    return _role


@router.get("/", response_model=schemas.ListResponse[schemas.Role], dependencies=[Depends(deps.get_current_active_user)])
def get_roles(
    *,
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = None,
    sort: Annotated[str | None, Query(...)] = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get all roles (paginated)
    """
    roles, count = crud.role.query_with_filters(db, None, None, sort, skip, limit)
    return {"totalCount": count, "resultCount": len(roles), "result": roles}


@router.delete("/{id}", response_model=schemas.Role, dependencies=[Depends(deps.admin_only)])
def delete_role(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    _: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
) -> Any:
    """
    Delete a role
    """
    _role = crud.role.get(db, id, audit_logger)
    if not _role:
        raise HTTPException(404, "Role not found")

    return crud.role.remove(db, _id=id, audit_logger=audit_logger)


@router.post("/assign", response_model=schemas.Msg, dependencies=[Depends(deps.admin_only)])
async def assign_role(
    username: Annotated[str, Query(...)],
    role_name: Annotated[str | None, Query(...)] = None,
    role_id: Annotated[int | None, Query(...)] = None,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Assign a role to a user
    """
    # Need exactly one of role_name or role_id
    if (role_name is None and role_id is None) or (
        role_name is not None and role_id is not None
    ):
        raise HTTPException(422, "Exactly one of role_name or role_id must be specified")
    role = None
    # Populate role via role_name or role_id
    if role_name is not None:
        role = crud.role.get_role_by_name(db, role_name)
    else:
        role = crud.role.get(db, role_id)
    if not role:
        raise HTTPException(404, f"Role {role_name if role_name else role_id} not found")
    # Get user
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(404, f"User {username} not found")
    # Add role to user (check for uniqueness)
    if role in user.roles:
        raise HTTPException(400, f"User {user.username} already has role {role.name}")
    # Log role assignment
    if audit_logger is not None:
        audit_logger.log("assign " + username, role)
    user.roles.append(role)
    db.add(user)
    return {"msg": f"Success: role {role.name} was assigned to {user.username}"}


@router.post("/remove", response_model=schemas.Msg, dependencies=[Depends(deps.admin_only)])
async def remove_role(
    username: Annotated[str, Query(...)],
    role_name: Annotated[str | None, Query(...)] = None,
    role_id: Annotated[int | None, Query(...)] = None,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Remove a role from a user
    """
    # Need exactly one of role_name or role_id
    if (role_name is None and role_id is None) or (
        role_name is not None and role_id is not None
    ):
        raise HTTPException(422, "Exactly one of role_name or role_id must be specified")
    role = None
    # Populate role via role_name or role_id
    if role_name is not None:
        role = crud.role.get_role_by_name(db, role_name)
    else:
        role = crud.role.get(db, role_id)
    if not role:
        raise HTTPException(404, f"Role {role_name if role_name else role_id} not found")
    # Get user
    user = crud.user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(404, f"User {username} not found")
    # Remove role from user
    if role not in user.roles:
        raise HTTPException(400, "User {username} does not have role {role.name}")
    # Log role revocation
    if audit_logger is not None:
        audit_logger.log("revoke " + username, role)
    user.roles.remove(role)
    db.add(user)
    return {"msg": f"Success: role {role.name} was removed from {user.username}"}
