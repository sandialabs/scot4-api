from sqlalchemy import func, inspect
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.audit import Audit
from app.schemas.audit import AuditCreate, AuditUpdate


class CRUDAudit(CRUDBase[Audit, AuditCreate, AuditUpdate]):
    def create_batch(self, db_session: Session, audits: list[AuditCreate]):
        db_objs = []

        for audit in audits:
            audit_data = audit.model_dump(exclude_unset=True)
            db_audit = Audit(**audit_data)
            db_objs.append(db_audit)
            db_session.add(db_audit)
        db_session.flush()
        return db_objs

    # Custom filtering for audits - what can accept string fragments
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "what")

        return super().filter(query, filter_dict)

    # Speed up audit counting since audit permissions come from elsewhere
    def get_count_from_query(self, query):
        return (
            query.group_by(None)
            .with_entities(func.count(inspect(self.model).primary_key[0]))
            .scalar()
        )


audit = CRUDAudit(Audit)
