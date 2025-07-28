import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum
from app.models import Feed, Feed
from app.schemas.feed import FeedCreate, FeedUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.feed import create_random_feed
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_feed(db: Session, faker: Faker) -> None:
    feed = create_random_feed(db, faker)
    db_obj = crud.feed.get(db, feed.id)

    assert db_obj.id == feed.id

    db_obj = crud.feed.get(db, -1)

    assert db_obj is None


def test_get_multi_feed(db: Session, faker: Faker) -> None:
    feeds = []
    for _ in range(5):
        feeds.append(create_random_feed(db, faker))

    db_objs = crud.feed.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == feeds[0].id for i in db_objs)

    db_objs = crud.feed.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == feeds[1].id for i in db_objs)

    db_objs = crud.feed.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.feed.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    feed = FeedCreate(
        name=faker.word(),
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=faker.word(),
        type=faker.word(),
        uri=faker.uri(),
        article_count=faker.pyint(),
        promotions_count=faker.pyint(),
    )
    db_obj = crud.feed.create(db, obj_in=feed)

    assert db_obj.id is not None
    assert db_obj.name == feed.name
    assert db_obj.owner == feed.owner
    assert db_obj.tlp == feed.tlp
    assert db_obj.status == feed.status
    assert db_obj.type == feed.type
    assert db_obj.uri == feed.uri
    assert db_obj.article_count == feed.article_count
    assert db_obj.promotions_count == feed.promotions_count


def test_update_feed(db: Session, faker: Faker) -> None:
    feed = create_random_feed(db, faker)
    owner = create_random_user(db, faker)
    update = FeedUpdate(
        name=faker.word(),
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=faker.word(),
        type=faker.word(),
        uri=faker.uri(),
        article_count=faker.pyint(),
        promotions_count=faker.pyint(),
    )

    db_obj = crud.feed.update(db, db_obj=feed, obj_in=update)

    assert db_obj.id == feed.id
    assert db_obj.name == update.name
    assert db_obj.owner == update.owner
    assert db_obj.tlp == update.tlp
    assert db_obj.status == update.status
    assert db_obj.type == update.type
    assert db_obj.uri == update.uri
    assert db_obj.article_count == update.article_count
    assert db_obj.promotions_count == update.promotions_count

    update = {}

    db_obj = crud.feed.update(db, db_obj=feed, obj_in=update)

    assert db_obj.id == feed.id

    update = {
        "test": "test"
    }

    db_obj = crud.feed.update(db, db_obj=feed, obj_in=update)

    assert db_obj.id == feed.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "name": faker.word(),
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "status": faker.word(),
        "type": faker.word(),
        "uri": faker.uri(),
        "article_count": faker.pyint(),
        "promotions_count": faker.pyint(),
    }

    db_obj = crud.feed.update(db, db_obj=Feed(), obj_in=update)

    assert db_obj.name == update["name"]
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.status == update["status"]
    assert db_obj.type == update["type"]
    assert db_obj.uri == update["uri"]
    assert db_obj.article_count == update["article_count"]
    assert db_obj.promotions_count == update["promotions_count"]


def test_remove_feed(db: Session, faker: Faker) -> None:
    feed = create_random_feed(db, faker)

    db_obj = crud.feed.remove(db, _id=feed.id)

    assert db_obj.id == feed.id

    db_obj_del = crud.feed.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.feed.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    feed = FeedCreate(
        name=faker.word(),
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=faker.word(),
        type=faker.word(),
        uri=faker.uri(),
        article_count=faker.pyint(),
        promotions_count=faker.pyint(),
    )

    db_obj = crud.feed.get_or_create(db, obj_in=feed)

    assert db_obj.id is not None

    same_db_obj = crud.feed.get_or_create(db, obj_in=feed)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    feeds = []
    for _ in range(5):
        feeds.append(create_random_feed(db, faker, owner))

    random_feed = random.choice(feeds)

    db_obj, count = crud.feed.query_with_filters(db, filter_dict={"id": random_feed.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_feed.id

    db_obj, count = crud.feed.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(feeds)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.feed.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(feeds) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.feed.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.feed.query_with_filters(db, filter_dict={"uri": f"!{random_feed.uri}"})

    assert db_obj is not None
    assert all(a.uri != random_feed.uri for a in db_obj)


def test_get_with_roles_feed(db: Session, faker: Faker) -> None:
    feeds = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        feed = FeedCreate(
            name=faker.word(),
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=faker.word(),
            type=faker.word(),
            uri=faker.uri(),
            article_count=faker.pyint(),
            promotions_count=faker.pyint(),
        )
        roles.append(role)

        feeds.append(crud.feed.create_with_permissions(db, obj_in=feed, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.feed.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_feed(db: Session, faker: Faker) -> None:
    feeds = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        feed = FeedCreate(
            name=faker.word(),
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            status=faker.word(),
            type=faker.word(),
            uri=faker.uri(),
            article_count=faker.pyint(),
            promotions_count=faker.pyint(),
        )
        roles.append(role)

        feeds.append(crud.feed.create_with_permissions(db, obj_in=feed, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.feed.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_feed(db: Session, faker: Faker) -> None:
    feed = FeedCreate(
        name=faker.word(),
        tlp=random.choice(list(TlpEnum)),
        status=faker.word(),
        type=faker.word(),
        uri=faker.uri(),
        article_count=faker.pyint(),
        promotions_count=faker.pyint(),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.feed.create_with_owner(db, obj_in=feed, owner=owner)

    assert db_obj is not None
    assert db_obj.name == feed.name
    assert db_obj.tlp == feed.tlp
    assert db_obj.status == feed.status
    assert db_obj.type == feed.type
    assert db_obj.uri == feed.uri
    assert db_obj.article_count == feed.article_count
    assert db_obj.promotions_count == feed.promotions_count
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_feed(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    feed = FeedCreate(
        name=faker.word(),
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=faker.word(),
        type=faker.word(),
        uri=faker.uri(),
        article_count=faker.pyint(),
        promotions_count=faker.pyint(),
    )

    db_obj = crud.feed.create_with_permissions(db, obj_in=feed, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.name == feed.name
    assert db_obj.owner == feed.owner
    assert db_obj.tlp == feed.tlp
    assert db_obj.status == feed.status
    assert db_obj.type == feed.type
    assert db_obj.uri == feed.uri
    assert db_obj.article_count == feed.article_count
    assert db_obj.promotions_count == feed.promotions_count

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.feed, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    feed = FeedCreate(
        name=faker.word(),
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=faker.word(),
        type=faker.word(),
        uri=faker.uri(),
        article_count=faker.pyint(),
        promotions_count=faker.pyint(),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.feed.create_in_object(db, obj_in=feed, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.name == feed.name

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_feed(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    feed = FeedCreate(
        name=faker.word(),
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        status=faker.word(),
        type=faker.word(),
        uri=faker.uri(),
        article_count=faker.pyint(),
        promotions_count=faker.pyint(),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.feed.create(db, obj_in=feed, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.feed.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_feed(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    feed = create_random_feed(db, faker, user)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.feed.remove(db, _id=feed.id, audit_logger=audit_logger)

    assert db_obj.id == feed.id

    db_obj = crud.feed.undelete(db, db_obj.id)

    assert db_obj is None
