from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import TargetTypeEnum

from .generic import generic_search

router = APIRouter()

# Note: stats are not populated by the api yet
generic_search(router, crud.stat, TargetTypeEnum.stat, schemas.StatSearch, schemas.Stat)


@router.get("/{id}", response_model=schemas.Stat)
def read_stat(
    *,
    db: Session = Depends(deps.get_db),
    id: Annotated[int, Path(...)],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get stat by ID
    """
    _stat = crud.stat.get(db_session=db, _id=id)
    if not _stat:
        raise HTTPException(404, "Stat object not found")

    return _stat


# TODO: stats in other endpoint paths (e.g. /entity/{id}/stat)
