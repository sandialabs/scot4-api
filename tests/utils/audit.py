import json
import random
from faker import Faker
from typing import Any
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.deps import AUDIT_DATA_VERSION
from app.db.base_class import Base
from app.enums import TargetTypeEnum


def create_audit(db: Session, faker: Faker, username: str, db_obj: Any, source: Any | None = None, user_agent: str | None = None):
    thing_type = TargetTypeEnum.none
    if isinstance(db_obj, Base):
        thing_type = db_obj.target_type_enum()
    if thing_type == TargetTypeEnum.none:
        thing_type = type(db_obj).__name__.lower()
    elif not isinstance(thing_type, (str, TargetTypeEnum)):
        thing_type = thing_type.__name__.lower()
    if isinstance(thing_type, TargetTypeEnum):
        thing_type = str(thing_type.value)

    if source is None:
        source = faker.ipv4()
    if user_agent is None:
        user_agent = faker.user_agent()

    what = random.choice(["create", "delete", "update"])

    data = json.dumps(jsonable_encoder(db_obj.as_dict()))
    audit = schemas.AuditCreate(
        when_date=datetime.utcnow(),
        username=username,
        what=what,
        thing_type=thing_type,
        thing_id=db_obj.id,
        src_ip=str(source),
        user_agent=user_agent,
        audit_data_ver=AUDIT_DATA_VERSION,
        audit_data=data,
    )

    return crud.audit.create(db, obj_in=audit)
