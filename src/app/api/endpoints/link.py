from typing import Any, Annotated
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import TargetTypeEnum

from .generic import generic_delete, generic_get, generic_post, generic_put, generic_search

router = APIRouter()

# Create get, post, put, and delete endpoints
generic_get(router, crud.link, TargetTypeEnum.none, schemas.Link, "Link")
# TODO: Permissions on who can link what to what?
generic_post(router, crud.link, TargetTypeEnum.none, schemas.Link, schemas.LinkCreate, "Link", False, False)
generic_put(router, crud.link, TargetTypeEnum.none, schemas.Link, schemas.LinkUpdate, "Link")
generic_delete(router, crud.link, TargetTypeEnum.none, schemas.Link, "Link")
generic_search(router, crud.link, TargetTypeEnum.none, schemas.LinkSearch, schemas.Link, "Link")

# Most relevant link stuff is handled via other endpoints on the linked objects


@router.post(
    "/deletebetween",
    response_model=list[schemas.Link],
    summary="Delete links between two objects"
)
def delete_links_between_objects(
    *,
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    v0_type: Annotated[TargetTypeEnum, Body(...)],
    v0_id: Annotated[int, Body(...)],
    v1_type: Annotated[TargetTypeEnum, Body(...)],
    v1_id: Annotated[int, Body(...)],
    bidirectional: Annotated[bool, Body()] = False,
) -> Any:
    """
    Deletes all links from object (v0_type, v0_id) to object (v1_type, v1_id).
    Also deletes links in the other direction if the bidirectional parameter
    is set to true.
    """
    deleted = crud.link.delete_links(db, v0_type, v0_id, v1_type, v1_id, bidirectional, audit_logger)
    if deleted is None:
        raise HTTPException(404, "No links found to delete")
    return deleted
