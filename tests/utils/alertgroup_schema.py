import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.schemas.alertgroupschema import AlertGroupSchemaColumnCreate


def create_random_schema(faker: Faker, alertgroup_id: int | None = None, db: Session | None = None):
    base_schema = ["mac", "id", "mail", "url", "v4_ip", "v6_ip"]
    if db is not None:
        schema_type = random.choice(base_schema)
        schema = AlertGroupSchemaColumnCreate(
            alertgroup_id=alertgroup_id,
            schema_key_name=f"{faker.word()}_{schema_type}",
            schema_key_type=schema_type,
            schema_key_order=0
        )

        return crud.alert_group_schema.create(db, obj_in=schema)
    else:
        schemas = []
        for k in range(faker.pyint(1, len(base_schema))):
            schema = AlertGroupSchemaColumnCreate(
                schema_key_name=f"{faker.word()}_{base_schema[k]}",
                schema_key_type=base_schema[k],
                schema_key_order=k
            )

            schemas.append(schema)

        return schemas
