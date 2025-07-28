from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.special_metric import SpecialMetric
from app.schemas.special_metric import SpecialMetricCreate, SpecialMetricUpdate


class CRUDSpecialMetric(CRUDBase[SpecialMetric, SpecialMetricCreate, SpecialMetricUpdate]):
    def get_or_create(
        self, db_session: Session, obj_in: SpecialMetricCreate, audit_logger=None
    ) -> SpecialMetric:
        instance = (
            db_session.query(self.model)
            .filter(self.model.target_type == obj_in.target_type)
            .filter(self.model.target_id == obj_in.target_id)
            .filter(self.model.metric_type == obj_in.metric_type)
            .all()
        )
        if len(instance) > 0:
            instance = instance[0]  # this is to compensate for duplicate entry values for the time being.
            if audit_logger is not None:
                audit_logger.log("read", instance, log_thing=False)
            return instance
        else:
            if isinstance(obj_in, SpecialMetricCreate):
                obj_in_data = obj_in.model_dump(exclude_unset=True)
            else:
                obj_in_data = jsonable_encoder(obj_in)

            db_obj = self.model(**obj_in_data)
            db_session.add(db_obj)
            db_session.flush()
            db_session.refresh(db_obj)
            if audit_logger is not None:
                audit_logger.log("create", db_obj)
            return db_obj


special_metric = CRUDSpecialMetric(SpecialMetric)
