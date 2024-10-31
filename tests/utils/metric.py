from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.audit import Audit
from app.schemas.metric import MetricCreate

try:
    from tests.utils.alert import create_random_alert
    from tests.utils.audit import create_audit
    from tests.utils.user import create_random_user
except ImportError:
    from alert import create_random_alert
    from audit import create_audit
    from user import create_random_user


def create_random_metric(db: Session, faker: Faker, audit: Audit | None = None):
    if audit is None:
        user = create_random_user(db, faker)
        alert = create_random_alert(db, faker, user.username)
        audit = create_audit(db, faker, user.username, alert)
    metric = MetricCreate(
        name=faker.word(),
        tooltip=faker.sentence(),
        parameters={
            "what": audit.what,
            "type": audit.thing_type,
            "id": audit.thing_id,
            "data": audit.audit_data
        }
    )

    return crud.metric.create(db, obj_in=metric)
