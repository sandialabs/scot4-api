from typing import Any, Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Body, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.utils import create_schema_details

router = APIRouter()
description, examples = create_schema_details(schemas.GameCreate)


# Reads ALL gamification data
# Open to all users
@router.get("/", response_model=list[schemas.Game])
def read_games(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get ALL gamification data (no pagination)
    """
    games = crud.game.get_multi(db_session=db)
    return games


# Creates a new game
# Admin only
@router.post("/", response_model=schemas.Game, summary="Create a game", description=description)
def create_game(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    game: Annotated[schemas.GameCreate, Body(..., openapi_examples=examples)],
) -> Any:
    """
    Creates a gamification category. `name` is the category's short name
    (e.g. "Closer"), `tooltip` is a description of the category (e.g.
    "Most Alerts Closed"), and `parameters` is a dictionary describing the
    conditions being tracked. The available parameters are:
     * "what" - the action being taken, in the set ["create", "read",
                 "update", "delete", "undelete", "login"]
     * "type" - the type of thing being acted upon
     * "id" - the id of the thing being acted upon
     * "data" - a dictionary whose data must match the data in the event

    For example, a parameters dictionary of
        `{"what": "update", "type": "alert", "data": {"status": "closed"}}`
    would count the number of alert-closing events by each user.
    """
    return crud.game.create(db_session=db, obj_in=game, audit_logger=audit_logger)


@router.get("/results", response_model=list[schemas.GameResult], summary="Get game results")
def get_results(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    game_ids: Annotated[list[int] | None, Query(...)] = None,
    dates: Annotated[list[datetime] | None, Query(..., min_items=1, max_items=2)] = None,
    num_top_users: Annotated[int | None, Query(...)] = None,
    exclude_users: Annotated[list[str] | None, Query(...)] = None,
) -> Any:
    return crud.game.get_results_for_games(
        db_session=db,
        game_ids=game_ids,
        date_range=dates,
        num_top_users=num_top_users,
        exclude_users=exclude_users
    )


# Gets single gamification data
# Open to all users
@router.get("/{id}", response_model=schemas.Game)
def read_game(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    id: Annotated[int, Path(...)]
) -> Any:
    """
    Get the data of a game
    """
    _game = crud.game.get(db_session=db, _id=id)
    if _game:
        return _game
    else:
        raise HTTPException(404, f"game {id} not found")
