import random
from datetime import timedelta
from fastapi.encoders import jsonable_encoder
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum, StatusEnum
from app.models import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.incident import create_random_incident
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role
from tests.utils.event import create_random_event


def test_get_incident(db: Session, faker: Faker) -> None:
    incident = create_random_incident(db, faker, create_extras=False)
    db_obj = crud.incident.get(db, incident.id)

    assert db_obj.id == incident.id

    db_obj = crud.incident.get(db, -1)

    assert db_obj is None


def test_get_multi_incident(db: Session, faker: Faker) -> None:
    incidents = []
    for _ in range(3):
        incidents.append(create_random_incident(db, faker, create_extras=False))

    db_objs = crud.incident.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == incidents[0].id for i in db_objs)

    db_objs = crud.incident.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == incidents[1].id for i in db_objs)

    db_objs = crud.incident.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.incident.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_incident(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    occurred_date = faker.past_datetime()
    discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
    incident = IncidentCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        occurred_date=occurred_date,
        discovered_date=discovered_date,
        reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
        view_count=faker.pyint()
    )
    db_obj = crud.incident.create(db, obj_in=incident)

    assert db_obj.id is not None
    assert db_obj.owner == incident.owner
    assert db_obj.tlp == incident.tlp
    assert db_obj.occurred_date.replace(tzinfo=None) == incident.occurred_date
    assert db_obj.discovered_date.replace(tzinfo=None) == incident.discovered_date
    assert db_obj.reported_date.replace(tzinfo=None) == incident.reported_date
    assert db_obj.status == incident.status
    assert db_obj.subject == incident.subject
    assert db_obj.data_ver == incident.data_ver
    assert db_obj.data == incident.data
    assert db_obj.view_count == incident.view_count


def test_update_incident(db: Session, faker: Faker) -> None:
    incident = create_random_incident(db, faker, create_extras=False)
    owner = create_random_user(db, faker)
    occurred_date = faker.past_datetime()
    discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
    update = IncidentUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        occurred_date=occurred_date,
        discovered_date=discovered_date,
        reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
        view_count=faker.pyint()
    )

    db_obj = crud.incident.update(db, db_obj=incident, obj_in=update)

    assert db_obj.id == incident.id
    assert db_obj.owner == update.owner
    assert db_obj.tlp == update.tlp
    assert db_obj.occurred_date.replace(tzinfo=None) == update.occurred_date
    assert db_obj.discovered_date.replace(tzinfo=None) == update.discovered_date
    assert db_obj.reported_date.replace(tzinfo=None) == update.reported_date
    assert db_obj.status == update.status
    assert db_obj.subject == update.subject
    assert db_obj.data_ver == update.data_ver
    assert db_obj.data == update.data
    assert db_obj.view_count == update.view_count

    update = {}

    db_obj = crud.incident.update(db, db_obj=incident, obj_in=update)

    assert db_obj.id == incident.id

    update = {
        "test": "test"
    }

    db_obj = crud.incident.update(db, db_obj=incident, obj_in=update)

    assert db_obj.id == incident.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    occurred_date = faker.past_datetime()
    discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "occurred_date": occurred_date,
        "discovered_date": discovered_date,
        "reported_date": discovered_date + timedelta(days=faker.pyint(1, 10)),
        "status": random.choice(list(StatusEnum)),
        "subject": faker.sentence(),
        "data_ver": str(faker.pyfloat(1, 1, True)),
        "data": jsonable_encoder(faker.pydict()),
        "view_count": faker.pyint()
    }

    db_obj = crud.incident.update(db, db_obj=Incident(), obj_in=update)

    assert db_obj.id == incident.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.occurred_date.replace(tzinfo=None) == update["occurred_date"]
    assert db_obj.discovered_date.replace(tzinfo=None) == update["discovered_date"]
    assert db_obj.reported_date.replace(tzinfo=None) == update["reported_date"]
    assert db_obj.status == update["status"]
    assert db_obj.subject == update["subject"]
    assert db_obj.data_ver == update["data_ver"]
    assert db_obj.data == update["data"]
    assert db_obj.view_count == update["view_count"]


def test_remove_incident(db: Session, faker: Faker) -> None:
    incident = create_random_incident(db, faker, create_extras=False)

    db_obj = crud.incident.remove(db, _id=incident.id)

    assert db_obj.id == incident.id

    db_obj_del = crud.incident.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.incident.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_incident(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    occurred_date = faker.past_datetime()
    discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
    incident = IncidentCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        occurred_date=occurred_date,
        discovered_date=discovered_date,
        reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
        view_count=faker.pyint()
    )

    db_obj = crud.incident.get_or_create(db, obj_in=incident)

    assert db_obj.id is not None

    same_db_obj = crud.incident.get_or_create(db, obj_in=incident)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_incident(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    incidents = []
    for _ in range(3):
        incidents.append(create_random_incident(db, faker, owner, create_extras=False))

    random_incident = random.choice(incidents)

    db_obj, count = crud.incident.query_with_filters(db, filter_dict={"id": random_incident.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_incident.id

    db_obj, count = crud.incident.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(incidents)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.incident.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(incidents) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.incident.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.incident.query_with_filters(db, filter_dict={"subject": random_incident.subject})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0].id == random_incident.id

    event = create_random_event(db, faker)
    promote = crud.promotion.promote(db, [{"type": TargetTypeEnum.event, "id": event.id}], TargetTypeEnum.incident)

    db_obj, count = crud.incident.query_with_filters(db, filter_dict={"promoted_from": f"{TargetTypeEnum.event.value}:{event.id}"})

    assert db_obj is not None
    assert any(i.id == promote.id for i in db_obj)

    db_obj, count = crud.incident.query_with_filters(db, filter_dict={"not": {"subject": random_incident.subject}})
    assert db_obj is not None
    assert all(a.subject != random_incident.subject for a in db_obj)


def test_get_with_roles_incident(db: Session, faker: Faker) -> None:
    incidents = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        occurred_date = faker.past_datetime()
        discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
        incident = IncidentCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            occurred_date=occurred_date,
            discovered_date=discovered_date,
            reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
            data_ver=str(faker.pyfloat(1, 1, True)),
            data=jsonable_encoder(faker.pydict()),
            view_count=faker.pyint()
        )
        roles.append(role)

        incidents.append(crud.incident.create_with_permissions(db, obj_in=incident, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.incident.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_incident(db: Session, faker: Faker) -> None:
    incidents = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        occurred_date = faker.past_datetime()
        discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
        incident = IncidentCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            occurred_date=occurred_date,
            discovered_date=discovered_date,
            reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
            data_ver=str(faker.pyfloat(1, 1, True)),
            data=jsonable_encoder(faker.pydict()),
            view_count=faker.pyint()
        )
        roles.append(role)

        incidents.append(crud.incident.create_with_permissions(db, obj_in=incident, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.incident.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_incident(db: Session, faker: Faker) -> None:
    occurred_date = faker.past_datetime()
    discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
    incident = IncidentCreate(
        tlp=random.choice(list(TlpEnum)),
        occurred_date=occurred_date,
        discovered_date=discovered_date,
        reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
        view_count=faker.pyint()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.incident.create_with_owner(db, obj_in=incident, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == incident.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_incident(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    occurred_date = faker.past_datetime()
    discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
    incident = IncidentCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        occurred_date=occurred_date,
        discovered_date=discovered_date,
        reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
        view_count=faker.pyint()
    )

    db_obj = crud.incident.create_with_permissions(db, obj_in=incident, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == incident.owner
    assert db_obj.tlp == incident.tlp
    assert db_obj.occurred_date.replace(tzinfo=None) == incident.occurred_date
    assert db_obj.discovered_date.replace(tzinfo=None) == incident.discovered_date
    assert db_obj.reported_date.replace(tzinfo=None) == incident.reported_date
    assert db_obj.status == incident.status
    assert db_obj.subject == incident.subject
    assert db_obj.data_ver == incident.data_ver
    assert db_obj.data == incident.data
    assert db_obj.view_count == incident.view_count

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.incident, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_incident(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    occurred_date = faker.past_datetime()
    discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
    incident = IncidentCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        occurred_date=occurred_date,
        discovered_date=discovered_date,
        reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
        view_count=faker.pyint()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.incident.create_in_object(db, obj_in=incident, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == incident.subject

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_incident(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    occurred_date = faker.past_datetime()
    discovered_date = occurred_date + timedelta(days=faker.pyint(1, 10))
    incident = IncidentCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        occurred_date=occurred_date,
        discovered_date=discovered_date,
        reported_date=discovered_date + timedelta(days=faker.pyint(1, 10)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
        view_count=faker.pyint()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.incident.create(db, obj_in=incident, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.incident.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_incident(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    incident = create_random_incident(db, faker, user, create_extras=False)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.incident.remove(db, _id=incident.id, audit_logger=audit_logger)

    assert db_obj.id == incident.id

    db_obj = crud.incident.undelete(db, db_obj.id)

    assert db_obj is None


def test_increment_view_count(db: Session, faker: Faker) -> None:
    incident = create_random_incident(db, faker, create_extras=False)
    view_count = incident.view_count

    crud.incident.increment_view_count(db, incident.id)
    db_obj = crud.incident.get(db, incident.id)

    assert db_obj is not None
    assert db_obj.view_count == view_count + 1
