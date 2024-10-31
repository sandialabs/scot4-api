import random

from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum, StatusEnum
from app.models import VulnFeed
from app.schemas.vuln_feed import VulnFeedCreate, VulnFeedUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.vuln_feed import create_random_vuln_feed
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_vuln_feed(db: Session, faker: Faker) -> None:
    vuln_feed = create_random_vuln_feed(db, faker, create_extras=False)
    db_obj = crud.vuln_feed.get(db, vuln_feed.id)

    assert db_obj.id == vuln_feed.id

    db_obj = crud.vuln_feed.get(db, -1)

    assert db_obj is None


def test_get_multi_vuln_feed(db: Session, faker: Faker) -> None:
    vuln_feeds = []
    for _ in range(3):
        vuln_feeds.append(create_random_vuln_feed(db, faker, create_extras=False))

    db_objs = crud.vuln_feed.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == vuln_feeds[0].id for i in db_objs)

    db_objs = crud.vuln_feed.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == vuln_feeds[1].id for i in db_objs)

    db_objs = crud.vuln_feed.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.vuln_feed.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_vuln_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = VulnFeedCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    db_obj = crud.vuln_feed.create(db, obj_in=vuln_feed)

    assert db_obj.id is not None
    assert db_obj.owner == vuln_feed.owner
    assert db_obj.tlp == vuln_feed.tlp
    assert db_obj.status == vuln_feed.status
    assert db_obj.subject == vuln_feed.subject
    assert db_obj.view_count == vuln_feed.view_count
    assert db_obj.message_id == vuln_feed.message_id


def test_update_vuln_feed(db: Session, faker: Faker) -> None:
    vuln_feed = create_random_vuln_feed(db, faker, create_extras=False)
    owner = create_random_user(db, faker)
    update = VulnFeedUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.vuln_feed.update(db, db_obj=vuln_feed, obj_in=update)

    assert db_obj.id == vuln_feed.id
    assert db_obj.owner == update.owner
    assert db_obj.subject == update.subject

    update = {}

    db_obj = crud.vuln_feed.update(db, db_obj=vuln_feed, obj_in=update)

    assert db_obj.id == vuln_feed.id

    update = {
        "test": "test"
    }

    db_obj = crud.vuln_feed.update(db, db_obj=vuln_feed, obj_in=update)

    assert db_obj.id == vuln_feed.id
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

    db_obj = crud.vuln_feed.update(db, db_obj=VulnFeed(), obj_in=update)

    assert db_obj.id == vuln_feed.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.status == update["status"]
    assert db_obj.status == update["status"]
    assert db_obj.view_count == update["view_count"]
    assert db_obj.message_id == update["message_id"]


def test_remove_vuln_feed(db: Session, faker: Faker) -> None:
    vuln_feed = create_random_vuln_feed(db, faker, create_extras=False)

    db_obj = crud.vuln_feed.remove(db, _id=vuln_feed.id)

    assert db_obj.id == vuln_feed.id

    db_obj_del = crud.vuln_feed.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.vuln_feed.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_vuln_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = VulnFeedCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.vuln_feed.get_or_create(db, obj_in=vuln_feed)

    assert db_obj.id is not None

    same_db_obj = crud.vuln_feed.get_or_create(db, obj_in=vuln_feed)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_vuln_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_feeds = []
    for _ in range(3):
        vuln_feeds.append(create_random_vuln_feed(db, faker, owner.username, create_extras=False))

    random_vuln_feed = random.choice(vuln_feeds)

    db_obj, count = crud.vuln_feed.query_with_filters(db, filter_dict={"id": random_vuln_feed.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_vuln_feed.id

    db_obj, count = crud.vuln_feed.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(vuln_feeds)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.vuln_feed.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(vuln_feeds) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.vuln_feed.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.vuln_feed.query_with_filters(db, filter_dict={"subject": random_vuln_feed.subject})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_vuln_feed.id

    vuln_feed = create_random_vuln_feed(db, faker, create_extras=False)
    promote = crud.promotion.promote(db, [{"type": TargetTypeEnum.vuln_feed, "id": vuln_feed.id}], TargetTypeEnum.incident)

    db_obj, count = crud.vuln_feed.query_with_filters(db, filter_dict={"promoted_to": f"{TargetTypeEnum.incident.value}:{promote.id}"})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == vuln_feed.id

    db_obj, count = crud.vuln_feed.query_with_filters(db, filter_dict={"subject": f"!{random_vuln_feed.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_vuln_feed.subject for a in db_obj)


def test_get_with_roles_vuln_feed(db: Session, faker: Faker) -> None:
    vuln_feeds = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        vuln_feed = VulnFeedCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
            view_count=faker.pyint(),
            message_id=faker.word()
        )
        roles.append(role)

        vuln_feeds.append(crud.vuln_feed.create_with_permissions(db, obj_in=vuln_feed, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.vuln_feed.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_vuln_feed(db: Session, faker: Faker) -> None:
    vuln_feeds = []
    roles = []
    for _ in range(3):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        vuln_feed = VulnFeedCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=random.choice(list(StatusEnum)),
            subject=faker.sentence(),
            view_count=faker.pyint(),
            message_id=faker.word()
        )
        roles.append(role)

        vuln_feeds.append(crud.vuln_feed.create_with_permissions(db, obj_in=vuln_feed, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.vuln_feed.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_vuln_feed(db: Session, faker: Faker) -> None:
    vuln_feed = VulnFeedCreate(
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.vuln_feed.create_with_owner(db, obj_in=vuln_feed, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == vuln_feed.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_vuln_feed(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    vuln_feed = VulnFeedCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    db_obj = crud.vuln_feed.create_with_permissions(db, obj_in=vuln_feed, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == vuln_feed.owner
    assert db_obj.tlp == vuln_feed.tlp
    assert db_obj.status == vuln_feed.status
    assert db_obj.subject == vuln_feed.subject
    assert db_obj.view_count == vuln_feed.view_count
    assert db_obj.message_id == vuln_feed.message_id

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.vuln_feed, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_vuln_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = VulnFeedCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.vuln_feed.create_in_object(db, obj_in=vuln_feed, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == vuln_feed.subject

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_vuln_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    vuln_feed = VulnFeedCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=random.choice(list(StatusEnum)),
        subject=faker.sentence(),
        view_count=faker.pyint(),
        message_id=faker.word()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.vuln_feed.create(db, obj_in=vuln_feed, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.vuln_feed.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_vuln_feed(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    vuln_feed = create_random_vuln_feed(db, faker, user.username, create_extras=False)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.vuln_feed.remove(db, _id=vuln_feed.id, audit_logger=audit_logger)

    assert db_obj.id == vuln_feed.id

    db_obj = crud.vuln_feed.undelete(db, db_obj.id)

    assert db_obj is None


def test_increment_view_count_vuln_feed(db: Session, faker: Faker) -> None:
    vuln_feed = create_random_vuln_feed(db, faker, create_extras=False)
    view_count = vuln_feed.view_count

    crud.vuln_feed.increment_view_count(db, vuln_feed.id)
    db_obj = crud.vuln_feed.get(db, vuln_feed.id)

    assert db_obj.id == vuln_feed.id
    assert db_obj.view_count == view_count + 1
