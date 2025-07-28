from typing import Any, Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Body, Path
from sqlalchemy.orm import Session
from pydantic.json_schema import SkipJsonSchema

from app import crud, models, schemas
from app.api import deps
from app.utils import create_schema_details

router = APIRouter()


# Reads ALL gamification data
# Open to all users
@router.get("/", summary="Get game data", response_model=list[schemas.Game])
def read_games(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get ALL gamification data (no pagination)
    """
    return crud.game.get_multi(db)


# Creates a new game
# Admin only
_, examples = create_schema_details(schemas.GameCreate)


@router.post("/", response_model=schemas.Game, summary="Create a game")
def create_game(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_superuser),
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
    return crud.game.create(db, obj_in=game, audit_logger=audit_logger)


@router.get("/results", response_model=list[schemas.GameResult], summary="Get game results")
def get_results(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    game_ids: Annotated[list[int] | SkipJsonSchema[None], Query(...)] = None,
    dates: Annotated[list[datetime] | SkipJsonSchema[None], Query(..., min_items=1, max_items=2)] = None,
    num_top_users: Annotated[int | SkipJsonSchema[None], Query(...)] = None,
    exclude_users: Annotated[list[str] | SkipJsonSchema[None], Query(...)] = None,
) -> Any:
    """
    Returns the result statistics of all games, giving the top users in each category
    """
    return crud.game.get_results_for_games(db, game_ids, dates, num_top_users, exclude_users)


# Gets single gamification data
# Open to all users
@router.get("/{id}", response_model=schemas.Game, summary="Get a game")
def read_game(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    id: Annotated[int, Path(...)]
) -> Any:
    """
    Get the data of a game
    """
    _game = crud.game.get(db, id)
    if _game:
        return _game
    else:
        raise HTTPException(404, f"game {id} not found")
