import json
from datetime import datetime

from sqlalchemy import func, literal_column, and_
from sqlalchemy.orm import Session

from app.enums import TargetTypeEnum
from app.crud.base import CRUDBase
from app.models.metric import Metric
from app.models.audit import Audit
from app.schemas.metric import MetricCreate, MetricUpdate


class CRUDMetric(CRUDBase[Metric, MetricCreate, MetricUpdate]):
    def get_results_for_metrics(
        self,
        db_session: Session,
        metric_ids: list[int] | None = None,
        date_range: list[datetime] | None = None,
        exclude_users: list[str] | None = None,
    ):
        # Get specified metrics
        if metric_ids:
            metric_query = db_session.query(Metric).filter(Metric.id.in_(metric_ids))
            metrics = metric_query.all()
        else:
            metrics = db_session.query(Metric).all()
        # Get the results from the audit table
        results = []
        metric: Metric
        for metric in metrics:
            query = db_session.query(Audit.when_date, func.count(Audit.when_date))
            if date_range and len(date_range) == 1:
                query = query.filter(Audit.when_date >= date_range[0])
            elif date_range and len(date_range) >= 2:
                query = query.filter(
                    and_(Audit.when_date >= date_range[0], Audit.when_date <= date_range[1]))
            if exclude_users is not None:
                query = query.filter(Audit.username.not_in(exclude_users))
            params = metric.parameters
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
            query = query.group_by(Audit.when_date)
            raw_dates = query.all()
            # condense 
            dates = {}
            for date in raw_dates:
                if dates.get(date[0].strftime("%Y-%m-%d")) is not None:
                    dates[date[0].strftime("%Y-%m-%d")] += date[1]
                else:
                    dates[date[0].strftime("%Y-%m-%d")] = date[1]
            result = {
                "name": metric.name,
                "tooltip": metric.tooltip,
                "results": dates
            }
            results.append(result)
        return results


metric = CRUDMetric(Metric)


"""
don't aggregate by username, aggregate by when_date and then utilize sql functions to help group that per day / week / etc

"""
