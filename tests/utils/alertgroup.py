import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import TargetTypeEnum, TlpEnum
from app.schemas.alertgroup import AlertGroupDetailedCreate

try:
    from tests.utils.alert import create_random_alert_object, create_random_schema
    from tests.utils.user import create_random_user
    from tests.utils.tag import create_random_tag
    from tests.utils.source import create_random_source
    from tests.utils.flair import create_flair_results
except ImportError:
    # needed to make initial_data.py function properly
    from alert import create_random_alert_object, create_random_schema
    from user import create_random_user
    from tag import create_random_tag
    from source import create_random_source
    from flair import create_flair_results


def create_random_alertgroup(db: Session, sig_names_types, unique_sig_types, faker: Faker, owner: str | None = None):
    """
    Create a random alertgroup with alerts and a schema included.
    """

    if owner is None:
        owner = create_random_user(db, faker).username

    tlp = random.choice(list(TlpEnum))
    alert_count = faker.pyint(2, 5)
    closed_count = faker.pyint(0, alert_count)
    open_count = alert_count - closed_count
    promoted_count = faker.pyint(0, alert_count)
    view_count = faker.pyint(0, 5)
    message_id = faker.pyint(0, 5)
    subject = faker.sentence()
    schema = create_random_schema(faker)

    alerts = []
    entities = {}
    for _ in range(0, alert_count):
        _alert, _entities = create_random_alert_object(schema, db, faker, owner)
        entities[_] = _entities
        alerts.append(_alert)

    none_weight = 10
    other_weights = int((100 - none_weight) / (len(unique_sig_types) - 1))
    weights = [other_weights for x in range(len(unique_sig_types) - 1)]
    weights.append(none_weight)
    generated_from_sig_type = random.choices(unique_sig_types, weights=weights, k=1)[0]

    if generated_from_sig_type != "None":
        # This means this alertgroup was generated from a 'signature' we have in SCOT.
        # So choose a signature name that corresponds with the type
        filtered_sigs = list(
            filter(lambda x: x["type"] == generated_from_sig_type, sig_names_types)
        )
        chosen_sig = random.choice(filtered_sigs)
        alert_group_title = f'({chosen_sig["type"]} Alert) {chosen_sig["name"]}'
        alertgroup_create = AlertGroupDetailedCreate(
            owner=owner,
            tlp=tlp,
            alert_count=alert_count,
            open_count=open_count,
            closed_count=closed_count,
            promoted_count=promoted_count,
            view_count=view_count,
            message_id=str(message_id),
            subject=alert_group_title,
            alerts=alerts,
            alert_schema=schema,
        )
    else:
        alertgroup_create = AlertGroupDetailedCreate(
            owner=owner,
            tlp=tlp,
            alert_count=alert_count,
            open_count=open_count,
            closed_count=closed_count,
            promoted_count=promoted_count,
            view_count=view_count,
            message_id=str(message_id),
            subject=subject,
            alerts=alerts,
            alert_schema=schema,
        )

    alert_group_crud = crud.alert_group.create(db, obj_in=alertgroup_create)

    for _ in range(random.randint(1, 5)):
        create_random_tag(db, faker, TargetTypeEnum.alertgroup, alert_group_crud.id)

    for _ in range(random.randint(1, 5)):
        create_random_source(db, faker, TargetTypeEnum.alertgroup, alert_group_crud.id)

    for c, alert in enumerate(alert_group_crud.alerts):
        _targets = [
            {"id": alert_group_crud.id, "type": TargetTypeEnum.alertgroup},
            {"id": alert.id, "type": TargetTypeEnum.alert}
        ]
        _entities = [{"type_name": x.type_name, "value": x.value} for x in entities[c]]
        create_flair_results(db, _targets, _entities)

    return alert_group_crud


def create_random_alertgroup_no_sig(db: Session, faker: Faker, owner: str | None = None, with_alerts: bool | None = True, parsed: bool | None = None):
    if owner is None:
        owner = create_random_user(db, faker).username

    alert_count = faker.pyint(2, 5)
    closed_count = faker.pyint(0, alert_count)
    subject = faker.sentence()
    alerts = []
    schema = None
    if with_alerts:
        schema = create_random_schema(faker)

        for _ in range(0, alert_count):
            alerts.append(create_random_alert_object(schema, db, faker, owner)[0])

    alertgroup_create = AlertGroupDetailedCreate(
        owner=owner,
        tlp=random.choice(list(TlpEnum)),
        alert_count=alert_count,
        open_count=alert_count - closed_count,
        closed_count=closed_count,
        promoted_count=faker.pyint(0, alert_count),
        view_count=faker.pyint(0, 5),
        message_id=str(faker.pyint(0, 5)),
        subject=subject,
        alerts=alerts,
        alert_schema=schema,
        first_view=faker.date_time_this_month()
    )

    return crud.alert_group.create(db, obj_in=alertgroup_create)
