import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud, schemas
from app.enums import StatusEnum, TlpEnum
from app.schemas.alert import AlertAdd, AlertCreate, AlertDataCreate, AlertGroupSchemaColumn

try:
    from tests.utils.alertgroup_schema import create_random_schema
    from tests.utils.entity import create_entity
    from tests.utils.user import create_random_user
except ImportError:
    # needed to make initial_data.py function properly
    from alertgroup_schema import create_random_schema
    from entity import create_entity
    from user import create_random_user


def create_data(schemas: list[AlertGroupSchemaColumn], faker: Faker):
    ioc_choices = {
        "mac": [faker.mac_address() for _ in range(100)],
        "id": [faker.md5() for _ in range(100)],
        "mail": [faker.email() for _ in range(100)],
        "v4_ip": [faker.ipv4() for _ in range(100)],
        "v6_ip": [faker.ipv6() for _ in range(100)],
        "url": [faker.url() for _ in range(100)],
    }
    alert_data = []
    alert_entities = []
    for s in schemas:
        key = s.schema_key_type
        before_string = faker.text(max_nb_chars=30)
        after_string = faker.text(max_nb_chars=30)
        if "mac" in key:
            data_value = random.choice(ioc_choices["mac"])
            entity = create_entity(data_value, "mac")
            data_value_flaired = f'<div> {before_string} <span class=entity data-entity-value={data_value} data-entity-type="mac"> {data_value} </span> {after_string} </div>'
            alert_entities.append(entity)

        if "id" in key:
            data_value = random.choice(ioc_choices["id"])
            entity = create_entity(data_value, "guid")
            data_value_flaired = f'<div> {before_string} <span class=entity data-entity-value={data_value} data-entity-type="guid"> {data_value} </span> {after_string} </div>'
            alert_entities.append(entity)

        if "v4" in key:
            data_value = random.choice(ioc_choices["v4_ip"])
            entity = create_entity(data_value, "ipv4")
            data_value_flaired = f'<div> {before_string} <span class=entity data-entity-value={data_value} data-entity-type="ipv4"> {data_value} </span> {after_string} </div>'
            alert_entities.append(entity)

        if "v6" in key:
            data_value = random.choice(ioc_choices["v6_ip"])
            entity = create_entity(data_value, "ipv6")
            alert_entities.append(entity)
            data_value_flaired = f'<div> {before_string} <span class=entity data-entity-value={data_value} data-entity-type="ipv6"> {data_value} </span> {after_string} </div>'

        if "mail" in key:
            data_value = random.choice(ioc_choices["mail"])
            entity = create_entity(data_value, "email")
            alert_entities.append(entity)
            entity = create_entity(data_value.split("@")[1], "domain")
            alert_entities.append(entity)
            data_value_flaired = f'<div>{before_string}<span class="entity email" data-entity-type="email" data-entity-value="{data_value}">{data_value.split("@")[0]}<span class="entity domain" data-entity-type="domain" data-entity-value="{data_value.split("@")[1]}">@{data_value.split("@")[1]}</span></span> {after_string}</div>'

        if "url" in key:
            data_value = random.choice(ioc_choices["url"])
            entity = create_entity(data_value, "url")
            alert_entities.append(entity)
            data_value_flaired = f'<div> {before_string} <span class=entity data-entity-value={data_value} data-entity-type="url"> {data_value} </span> {after_string} </div>'

        alert_data.append(
            AlertDataCreate(
                name=s.schema_key_name,
                value=data_value,
                value_flaired=data_value_flaired,
            )
        )

    return alert_data, alert_entities


def create_random_alert_object(schema: list, db: Session, faker: Faker, owner: schemas.User | None = None, parsed: bool | None = None):
    data, entity_ids = create_data(schema, faker)
    if owner is None:
        owner = create_random_user(db, faker)
    tlp = random.choice(list(TlpEnum))
    status = random.choice([StatusEnum.open, StatusEnum.closed])
    if parsed is None:
        parsed = faker.pybool()
    alert_create = AlertCreate(
        owner=owner.username, tlp=tlp, status=status, parsed=parsed, data=data
    )
    return alert_create, entity_ids


def create_random_alert(db: Session, faker: Faker, owner: schemas.User | None = None, schema: AlertGroupSchemaColumn | None = None, parsed: bool | None = None):
    if schema is None:
        schema = create_random_schema(faker)
    alert_create, _ = create_random_alert_object(schema, db, faker, owner, parsed)
    return crud.alert.create(db, obj_in=alert_create)


def create_random_alert_addition(db: Session, faker: Faker, owner: schemas.User | None = None):
    schema = create_random_schema(faker)
    data = create_data(schema, faker)[0]
    data = {d.name: d.value for d in data}
    if owner is None:
        owner = create_random_user(db, faker)
    tlp = random.choice(list(TlpEnum))
    location = faker.city()
    status = random.choice(list(StatusEnum))
    parsed = faker.pybool()
    alert_create = AlertAdd(
        owner=owner.username, tlp=tlp, location=location, status=status, parsed=parsed, data=data
    )

    return crud.alert.create(db, obj_in=alert_create)
