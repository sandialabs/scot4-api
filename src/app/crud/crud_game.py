import json
from datetime import datetime

from sqlalchemy import func, desc, literal_column, and_
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.models.game import Game
from app.models.audit import Audit
from app.schemas.game import GameCreate, GameUpdate


class CRUDGame(CRUDBase[Game, GameCreate, GameUpdate]):
    def get_results_for_games(
        self,
        db_session: Session,
        game_ids: list[int] | None = None,
        date_range: list[datetime] | None = None,
        num_top_users: int | None = None,
        exclude_users: list[str] | None = None,
    ):
        # Get specified games
        if game_ids:
            game_query = db_session.query(Game).filter(Game.id.in_(game_ids))
            games = game_query.all()
        else:
            games = db_session.query(Game).all()
        # Get the results from the audit table
        results = []
        game: Game
        for game in games:
            query = db_session.query(Audit.username, func.count(Audit.username))
            if date_range and len(date_range) == 1:
                query = query.filter(Audit.when_date >= date_range[0])
            elif date_range and len(date_range) >= 2:
                query = query.filter(
                    and_(Audit.when_date >= date_range[0], Audit.when_date <= date_range[1]))
            if exclude_users is not None:
                query = query.filter(Audit.username.not_in(exclude_users))
            params = game.parameters
            if "what" in params.keys():
                query = query.filter(Audit.what == params["what"])
            if "type" in params.keys():
                if params["type"] is None:
                    thing_type = type(TargetTypeEnum.none).__name__.lower()
                else:
                    thing_type = str(params["type"]).lower()
                query = query.filter(Audit.thing_type == thing_type)
            if "id" in params.keys():
                query = query.filter(Audit.thing_id == params["id"])
            if "data" in params.keys():
                if query.session.bind.dialect.name == "mysql":
                    # Special case for mysql so that indexes get used correctly
                    for key in params["data"]:
                        query = query.filter(
                            Audit.audit_data.op("->>")
                            (literal_column("\"$." + key + "\"")) == params["data"][key])
                elif query.session.bind.dialect.name == "postgresql":
                    for key in params["data"]:
                        if isinstance(params["data"][key], dict):
                            query = query.filter(Audit.audit_data[key].as_string() == json.dumps(params["data"][key]))
                        elif isinstance(params["data"][key], bool):
                            query = query.filter(Audit.audit_data[key].as_boolean() == params["data"][key])
                        else:
                            query = query.filter(Audit.audit_data[key].as_string() == str(params["data"][key]))
                else:
                    query = query.filter(Audit.audit_data.contains(params["data"]))
            query = query.group_by(Audit.username)
            query = query.order_by(desc(func.count(Audit.username)))
            if num_top_users is not None:
                query = query.limit(num_top_users)
            users = query.all()
            result = {
                "name": game.name,
                "tooltip": game.tooltip,
                "results": {u[0]: u[1] for u in users}
            }
            results.append(result)
        return results


game = CRUDGame(Game)
