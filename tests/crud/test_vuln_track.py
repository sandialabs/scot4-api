import random

from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum, StatusEnum
from app.models import VulnTrack
from app.schemas.vuln_track import VulnTrackCreate, VulnTrackUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.vuln_track import create_random_vuln_track
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_vuln_track(db: Session, faker: Faker) -> None:
    vuln_track = create_random_vuln_track(db, faker, create_extras=False)
    db_obj = crud.vuln_track.get(db, vuln_track.id)

    assert db_obj.id == vuln_track.id

    db_obj = crud.vuln_track.get(db, -1)

    assert db_obj is None


def test_get_multi_vuln_track(db: Session, faker: Faker) -> None:
    vuln_tracks = []
    for _ in range(3):
        vuln_tracks.append(create_random_vuln_track(db, faker, create_extras=False))

    db_objs = crud.vuln_track.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == vuln_tracks[0].id for i in db_objs)

    db_objs = crud.vuln_track.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == vuln_tracks[1].id for i in db_objs)

    db_objs = crud.vuln_track.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.vuln_track.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_vuln_track(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_track = VulnTrackCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    db_obj = crud.vuln_track.create(db, obj_in=vuln_track)

    assert db_obj.id is not None
    assert db_obj.owner == vuln_track.owner
    assert db_obj.tlp == vuln_track.tlp
    assert db_obj.status == vuln_track.status
    assert db_obj.subject == vuln_track.subject
    assert db_obj.view_count == vuln_track.view_count
    assert db_obj.message_id == vuln_track.message_id


def test_update_vuln_track(db: Session, faker: Faker) -> None:
    vuln_track = create_random_vuln_track(db, faker, create_extras=False)
    owner = create_random_user(db, faker)
    update = VulnTrackUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.vuln_track.update(db, db_obj=vuln_track, obj_in=update)

    assert db_obj.id == vuln_track.id
    assert db_obj.owner == update.owner
    assert db_obj.subject == update.subject

    update = {}

    db_obj = crud.vuln_track.update(db, db_obj=vuln_track, obj_in=update)

    assert db_obj.id == vuln_track.id

    update = {
        "test": "test"
    }

    db_obj = crud.vuln_track.update(db, db_obj=vuln_track, obj_in=update)

    assert db_obj.id == vuln_track.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "status": random.choice(list(StatusEnum)),
        "subject": faker.sentence(),
        "view_count": faker.pyint(),
        "message_id": faker.word()
    }

    db_obj = crud.vuln_track.update(db, db_obj=VulnTrack(), obj_in=update)

    assert db_obj.id == vuln_track.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.status == update["status"]
    assert db_obj.status == update["status"]
    assert db_obj.view_count == update["view_count"]
    assert db_obj.message_id == update["message_id"]


def test_remove_vuln_track(db: Session, faker: Faker) -> None:
    vuln_track = create_random_vuln_track(db, faker, create_extras=False)

    db_obj = crud.vuln_track.remove(db, _id=vuln_track.id)

    assert db_obj.id == vuln_track.id

    db_obj_del = crud.vuln_track.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.vuln_track.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_vuln_track(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_track = VulnTrackCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.vuln_track.get_or_create(db, obj_in=vuln_track)

    assert db_obj.id is not None

    same_db_obj = crud.vuln_track.get_or_create(db, obj_in=vuln_track)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_vuln_track(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_tracks = []
    for _ in range(3):
        vuln_tracks.append(create_random_vuln_track(db, faker, owner, create_extras=False))

    random_vuln_track = random.choice(vuln_tracks)

    db_obj, count = crud.vuln_track.query_with_filters(db, filter_dict={"id": random_vuln_track.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_vuln_track.id

    db_obj, count = crud.vuln_track.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(vuln_tracks)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.vuln_track.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(vuln_tracks) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.vuln_track.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.vuln_track.query_with_filters(db, filter_dict={"subject": random_vuln_track.subject})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_vuln_track.id

    vuln_track = create_random_vuln_track(db, faker, create_extras=False)
    promote = crud.promotion.promote(db, [{"type": TargetTypeEnum.vuln_track, "id": vuln_track.id}], TargetTypeEnum.incident)

    db_obj, count = crud.vuln_track.query_with_filters(db, filter_dict={"promoted_to": f"{TargetTypeEnum.incident.value}:{promote.id}"})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == vuln_track.id

    db_obj, count = crud.vuln_track.query_with_filters(db, filter_dict={"subject": f"!{random_vuln_track.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_vuln_track.subject for a in db_obj)


def test_get_with_roles_vuln_track(db: Session, faker: Faker) -> None:
    vuln_tracks = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        vuln_track = VulnTrackCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
            view_count=faker.pyint(),
            message_id=faker.word()
        )
        roles.append(role)

        vuln_tracks.append(crud.vuln_track.create_with_permissions(db, obj_in=vuln_track, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.vuln_track.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_vuln_track(db: Session, faker: Faker) -> None:
    vuln_tracks = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        vuln_track = VulnTrackCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
            view_count=faker.pyint(),
            message_id=faker.word()
        )
        roles.append(role)

        vuln_tracks.append(crud.vuln_track.create_with_permissions(db, obj_in=vuln_track, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.vuln_track.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_vuln_track(db: Session, faker: Faker) -> None:
    vuln_track = VulnTrackCreate(
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.vuln_track.create_with_owner(db, obj_in=vuln_track, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == vuln_track.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_vuln_track(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    vuln_track = VulnTrackCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.vuln_track.create_with_permissions(db, obj_in=vuln_track, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == vuln_track.owner
    assert db_obj.tlp == vuln_track.tlp
    assert db_obj.status == vuln_track.status
    assert db_obj.subject == vuln_track.subject
    assert db_obj.view_count == vuln_track.view_count
    assert db_obj.message_id == vuln_track.message_id

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.vuln_track, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_vuln_track(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_track = VulnTrackCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.vuln_track.create_in_object(db, obj_in=vuln_track, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == vuln_track.subject

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_vuln_track(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_track = VulnTrackCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.vuln_track.create(db, obj_in=vuln_track, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.vuln_track.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_vuln_track(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    vuln_track = create_random_vuln_track(db, faker, user, create_extras=False)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.vuln_track.remove(db, _id=vuln_track.id, audit_logger=audit_logger)

    assert db_obj.id == vuln_track.id

    db_obj = crud.vuln_track.undelete(db, db_obj.id)

    assert db_obj is None


def test_increment_view_count_vuln_track(db: Session, faker: Faker) -> None:
    vuln_track = create_random_vuln_track(db, faker, create_extras=False)
    view_count = vuln_track.view_count

    crud.vuln_track.increment_view_count(db, vuln_track.id)
    db_obj = crud.vuln_track.get(db, vuln_track.id)

    assert db_obj.id == vuln_track.id
    assert db_obj.view_count == view_count + 1
