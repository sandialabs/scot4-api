from typing import Any, Annotated
from fastapi import APIRouter, Depends, Path, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import TargetTypeEnum, PermissionEnum

from .generic import (
    generic_delete,
    generic_entries,
    generic_get,
    generic_post,
    generic_put,
    generic_undelete,
    generic_history,
    generic_entities,
    generic_search,
    generic_export
)

router = APIRouter()

# Create get, post, put, and delete endpoints
generic_export(router, crud.guide, TargetTypeEnum.guide)
generic_get(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_post(
    router, crud.guide, TargetTypeEnum.guide, schemas.Guide, schemas.GuideCreate
)
generic_put(
    router, crud.guide, TargetTypeEnum.guide, schemas.Guide, schemas.GuideUpdate
)
generic_delete(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_undelete(router, crud.guide, TargetTypeEnum.guide, schemas.Guide)
generic_entries(router, TargetTypeEnum.guide)
generic_entities(router, TargetTypeEnum.guide)
generic_history(router, crud.guide, TargetTypeEnum.guide)
generic_search(router, crud.guide, TargetTypeEnum.guide, schemas.GuideSearch, schemas.Guide)


@router.get(
    "/{id}/signatures", response_model=list[schemas.Signature],
    summary="Get signatures for guide",
    dependencies=[Depends(
        deps.PermissionCheckId(TargetTypeEnum.guide, PermissionEnum.read)
    )]
)
def signatures_for(
    *,
    roles: list[models.Role] = Depends(deps.get_current_roles),
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
) -> Any:
    _signatures = crud.guide.get_signatures_for(db, id, roles)
    if _signatures is None:
        raise HTTPException(404, f"Guide {id} not found")

    return _signatures
