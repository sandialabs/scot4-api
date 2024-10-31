import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.notification import create_random_notification
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_notification(db: Session, faker: Faker) -> None:
    notification = create_random_notification(db, faker)
    db_obj = crud.notification.get(db, notification.id)

    assert db_obj.id == notification.id

    db_obj = crud.notification.get(db, -1)

    assert db_obj is None


def test_get_multi_notification(db: Session, faker: Faker) -> None:
    notifications = []
    for _ in range(5):
        notifications.append(create_random_notification(db, faker))

    db_objs = crud.notification.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == notifications[0].id for i in db_objs)

    db_objs = crud.notification.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == notifications[1].id for i in db_objs)

    db_objs = crud.notification.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.notification.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_notification(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    notification = NotificationCreate(
        user_id=owner.id,
        message=faker.sentence(),
        ack=faker.pybool(),
        ref_id=faker.word()
    )
    db_obj = crud.notification.create(db, obj_in=notification)

    assert db_obj.id is not None
    assert db_obj.user_id == notification.user_id
    assert db_obj.message == notification.message
    assert db_obj.ack == notification.ack
    assert db_obj.ref_id == notification.ref_id


def test_update_notification(db: Session, faker: Faker) -> None:
    notification = create_random_notification(db, faker)
    owner = create_random_user(db, faker)
    update = NotificationUpdate(
        user_id=owner.id,
        message=faker.sentence(),
        ack=faker.pybool(),
        ref_id=faker.word()
    )

    db_obj = crud.notification.update(db, db_obj=notification, obj_in=update)

    assert db_obj.id == notification.id
    assert db_obj.user_id == update.user_id
    assert db_obj.message == update.message
    assert db_obj.ack == update.ack
    assert db_obj.ref_id == update.ref_id

    update = {}

    db_obj = crud.notification.update(db, db_obj=notification, obj_in=update)

    assert db_obj.id == notification.id

    update = {
        "test": "test"
    }

    db_obj = crud.notification.update(db, db_obj=notification, obj_in=update)

    assert db_obj.id == notification.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "user_id": owner.id,
        "message": faker.sentence(),
        "ack": faker.pybool(),
        "ref_id": faker.word()
    }

    db_obj = crud.notification.update(db, db_obj=Notification(), obj_in=update)

    assert db_obj.id == notification.id + 1
    assert db_obj.user_id == update["user_id"]
    assert db_obj.message == update["message"]
    assert db_obj.ack == update["ack"]
    assert db_obj.ref_id == update["ref_id"]


def test_remove_notification(db: Session, faker: Faker) -> None:
    notification = create_random_notification(db, faker)

    db_obj = crud.notification.remove(db, _id=notification.id)

    assert db_obj.id == notification.id

    db_obj_del = crud.notification.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.notification.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_notification(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    notification = NotificationCreate(
        user_id=owner.id,
        message=faker.sentence(),
        ack=faker.pybool(),
        ref_id=faker.word()
    )

    db_obj = crud.notification.get_or_create(db, obj_in=notification)

    assert db_obj.id is not None

    same_db_obj = crud.notification.get_or_create(db, obj_in=notification)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_notification(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    notifications = []
    for _ in range(5):
        notifications.append(create_random_notification(db, faker, owner.id))

    random_notification = random.choice(notifications)

    db_obj, count = crud.notification.query_with_filters(db, filter_dict={"id": random_notification.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_notification.id

    db_obj, count = crud.notification.query_with_filters(db, filter_dict={"user_id": owner.id})

    assert db_obj is not None
    assert len(db_obj) == len(notifications)
    assert len(db_obj) == count
    assert all(a.user_id == owner.id for a in db_obj)

    db_obj, count = crud.notification.query_with_filters(db, filter_dict={"user_id": owner.id}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(notifications) - 1
    assert len(db_obj) == count - 1
    assert all(a.user_id == owner.id for a in db_obj)

    db_obj, count = crud.notification.query_with_filters(db, filter_dict={"user_id": owner.id}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.user_id == owner.id for a in db_obj)

    db_obj, count = crud.notification.query_with_filters(db, filter_dict={"message": f"!{random_notification.message}"})

    assert db_obj is not None
    assert all(a.message != random_notification.message for a in db_obj)


def test_get_with_roles_notification(db: Session, faker: Faker) -> None:
    notifications = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        notification = NotificationCreate(
            user_id=owner.id,
            message=faker.sentence(),
            ack=faker.pybool(),
            ref_id=faker.word()
        )
        roles.append(role)

        notifications.append(crud.notification.create_with_permissions(db, obj_in=notification, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.notification.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_notification(db: Session, faker: Faker) -> None:
    notifications = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        notification = NotificationCreate(
            user_id=owner.id,
            message=faker.sentence(),
            ack=faker.pybool(),
            ref_id=faker.word()
        )
        roles.append(role)

        notifications.append(crud.notification.create_with_permissions(db, obj_in=notification, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.notification.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_notification(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    notification = NotificationCreate(
        user_id=owner.id,
        message=faker.sentence(),
        ack=faker.pybool(),
        ref_id=faker.word()
    )

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.notification.create_with_owner(db, obj_in=notification, owner=owner)

    assert db_obj is not None
    assert db_obj.message == notification.message
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_notification(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    notification = NotificationCreate(
        user_id=owner.id,
        message=faker.sentence(),
        ack=faker.pybool(),
        ref_id=faker.word()
    )

    db_obj = crud.notification.create_with_permissions(db, obj_in=notification, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.user_id == notification.user_id
    assert db_obj.message == notification.message
    assert db_obj.ack == notification.ack
    assert db_obj.ref_id == notification.ref_id


def test_create_in_object_notification(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    notification = NotificationCreate(
        user_id=owner.id,
        message=faker.sentence(),
        ack=faker.pybool(),
        ref_id=faker.word()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.notification.create_in_object(db, obj_in=notification, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.message == notification.message

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 0
    assert len(link) == 0


def test_get_history_notification(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    notification = NotificationCreate(
        user_id=owner.id,
        message=faker.sentence(),
        ack=faker.pybool(),
        ref_id=faker.word()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.notification.create(db, obj_in=notification, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.notification.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_notification(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    notification = create_random_notification(db, faker, user.id)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.notification.remove(db, _id=notification.id, audit_logger=audit_logger)

    assert db_obj.id == notification.id

    db_obj = crud.notification.undelete(db, db_obj.id)

    assert db_obj is None
