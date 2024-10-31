import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Link
from app.schemas.link import LinkCreate, LinkUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.alert import create_random_alert
from tests.utils.link import create_link
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user


def test_get_link(db: Session, faker: Faker) -> None:
    link = create_link(db, faker, TargetTypeEnum.alertgroup)
    db_obj = crud.link.get(db, link.id)

    assert db_obj.id == link.id

    db_obj = crud.link.get(db, -1)

    assert db_obj is None


def test_get_multi_link(db: Session, faker: Faker) -> None:
    links = []
    for _ in range(5):
        links.append(create_link(db, faker, TargetTypeEnum.alertgroup))

    db_objs = crud.link.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == links[0].id for i in db_objs)

    db_objs = crud.link.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == links[1].id for i in db_objs)

    db_objs = crud.link.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.link.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_link(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alert = create_random_alert(db, faker)
    link = LinkCreate(
        v0_type=TargetTypeEnum.alertgroup,
        v0_id=alertgroup.id,
        v1_type=TargetTypeEnum.alert,
        v1_id=alert.id
    )
    db_obj = crud.link.create(db, obj_in=link)

    assert db_obj.id is not None
    assert db_obj.v0_type == link.v0_type
    assert db_obj.v0_id == link.v0_id
    assert db_obj.v1_type == link.v1_type
    assert db_obj.v1_id == link.v1_id


def test_update_link(db: Session, faker: Faker) -> None:
    link = create_link(db, faker, TargetTypeEnum.alertgroup)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alert = create_random_alert(db, faker)
    update = LinkUpdate(
        v0_type=TargetTypeEnum.alertgroup,
        v0_id=alertgroup.id,
        v1_type=TargetTypeEnum.alert,
        v1_id=alert.id
    )

    db_obj = crud.link.update(db, db_obj=link, obj_in=update)

    assert db_obj.id == link.id
    assert db_obj.v0_type == update.v0_type
    assert db_obj.v0_id == update.v0_id
    assert db_obj.v1_type == update.v1_type
    assert db_obj.v1_id == update.v1_id

    update = {}

    db_obj = crud.link.update(db, db_obj=link, obj_in=update)

    assert db_obj.id == link.id

    update = {
        "test": "test"
    }

    db_obj = crud.link.update(db, db_obj=link, obj_in=update)

    assert db_obj.id == link.id
    assert not hasattr(db_obj, "test")

    link = create_link(db, faker, TargetTypeEnum.alertgroup)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alert = create_random_alert(db, faker)
    update = {
        "v0_type": TargetTypeEnum.alertgroup,
        "v0_id": alertgroup.id,
        "v1_type": TargetTypeEnum.alert,
        "v1_id": alert.id
    }

    db_obj = crud.link.update(db, db_obj=Link(), obj_in=update)

    assert db_obj.id == link.id + 1
    assert db_obj.v0_type == update["v0_type"]
    assert db_obj.v0_id == update["v0_id"]
    assert db_obj.v1_type == update["v1_type"]
    assert db_obj.v1_id == update["v1_id"]


def test_remove_link(db: Session, faker: Faker) -> None:
    link = create_link(db, faker, TargetTypeEnum.alertgroup)

    db_obj = crud.link.remove(db, _id=link.id)

    assert db_obj.id == link.id

    db_obj_del = crud.link.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.link.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_link(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alert = create_random_alert(db, faker)
    link = LinkCreate(
        v0_type=TargetTypeEnum.alertgroup,
        v0_id=alertgroup.id,
        v1_type=TargetTypeEnum.alert,
        v1_id=alert.id
    )

    db_obj = crud.link.get_or_create(db, obj_in=link)

    assert db_obj.id is not None

    same_db_obj = crud.link.get_or_create(db, obj_in=link)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_link(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker)
    links = []
    for _ in range(5):
        links.append(create_link(db, faker, TargetTypeEnum.alertgroup, alertgroup.id))

    random_link = random.choice(links)

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"id": random_link.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_link.id

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v1_id": alertgroup.id, "v1_type": TargetTypeEnum.alertgroup})

    assert db_obj is not None
    assert len(db_obj) == len(links)
    assert len(db_obj) == count
    assert all(a.v1_id == alertgroup.id for a in db_obj)

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v1_id": alertgroup.id, "v1_type": TargetTypeEnum.alertgroup}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(links) - 1
    assert len(db_obj) == count - 1
    assert all(a.v1_id == alertgroup.id for a in db_obj)

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"v1_id": alertgroup.id, "v1_type": TargetTypeEnum.alertgroup}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.v1_id == alertgroup.id for a in db_obj)

    db_obj, count = crud.link.query_with_filters(db, filter_dict={"context": f"!{random_link.context}"})

    assert db_obj is not None
    assert all(a.context != random_link.context for a in db_obj)


def test_get_with_roles_link(db: Session, faker: Faker) -> None:
    links = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
        alert = create_random_alert(db, faker)
        link = LinkCreate(
            v0_type=TargetTypeEnum.alertgroup,
            v0_id=alertgroup.id,
            v1_type=TargetTypeEnum.alert,
            v1_id=alert.id
        )
        roles.append(role)

        links.append(crud.link.create_with_permissions(db, obj_in=link, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.link.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_link(db: Session, faker: Faker) -> None:
    links = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
        alert = create_random_alert(db, faker)
        link = LinkCreate(
            v0_type=TargetTypeEnum.alertgroup,
            v0_id=alertgroup.id,
            v1_type=TargetTypeEnum.alert,
            v1_id=alert.id
        )
        roles.append(role)

        links.append(crud.link.create_with_permissions(db, obj_in=link, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.link.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_link(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alert = create_random_alert(db, faker)
    link = LinkCreate(
        v0_type=TargetTypeEnum.alertgroup,
        v0_id=alertgroup.id,
        v1_type=TargetTypeEnum.alert,
        v1_id=alert.id
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.link.create_with_owner(db, obj_in=link, owner=owner)

    assert db_obj is not None
    assert db_obj.v0_type == link.v0_type
    assert db_obj.v0_id == link.v0_id
    assert db_obj.v1_type == link.v1_type
    assert db_obj.v1_id == link.v1_id
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_link(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alert = create_random_alert(db, faker)
    link = LinkCreate(
        v0_type=TargetTypeEnum.alertgroup,
        v0_id=alertgroup.id,
        v1_type=TargetTypeEnum.alert,
        v1_id=alert.id
    )

    # dont have permissions but this should still create the link
    db_obj = crud.link.create_with_permissions(db, obj_in=link, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.v0_type == link.v0_type
    assert db_obj.v0_id == link.v0_id
    assert db_obj.v1_type == link.v1_type
    assert db_obj.v1_id == link.v1_id


def test_create_in_object_link(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alert = create_random_alert(db, faker)
    link = LinkCreate(
        v0_type=TargetTypeEnum.alertgroup,
        v0_id=alertgroup.id,
        v1_type=TargetTypeEnum.alert,
        v1_id=alert.id
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.link.create_in_object(db, obj_in=link, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.v0_id == link.v0_id

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 0
    assert len(link) == 0


def test_get_history_link(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    alert = create_random_alert(db, faker)
    link = LinkCreate(
        v0_type=TargetTypeEnum.alertgroup,
        v0_id=alertgroup.id,
        v1_type=TargetTypeEnum.alert,
        v1_id=alert.id
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.link.create(db, obj_in=link, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.link.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_link(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    link = create_link(db, faker, user.username)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.link.remove(db, _id=link.id, audit_logger=audit_logger)

    assert db_obj.id == link.id

    db_obj = crud.link.undelete(db, db_obj.id)

    assert db_obj is None


def test_delete_links(db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    # bidirectional links
    link1 = create_link(db, faker, TargetTypeEnum.alert, alert.id, TargetTypeEnum.alertgroup, alertgroup.id)
    link2 = create_link(db, faker, TargetTypeEnum.alertgroup, alertgroup.id, TargetTypeEnum.alert, alert.id)

    db_obj = crud.link.delete_links(db, TargetTypeEnum.none, -1, TargetTypeEnum.none, -1)

    assert db_obj is None

    db_obj = crud.link.delete_links(db, TargetTypeEnum.alertgroup, alertgroup.id, TargetTypeEnum.alert, alert.id)

    assert len(db_obj) == 2
    assert link1.id in [i.id for i in db_obj]
    assert link2.id in [i.id for i in db_obj]

    link_obj = crud.link.get(db, link1.id)

    assert link_obj is None

    link_obj = crud.link.get(db, link2.id)

    assert link_obj is None

    # bidirectional links
    link1 = create_link(db, faker, TargetTypeEnum.alert, alert.id, TargetTypeEnum.alertgroup, alertgroup.id)
    link2 = create_link(db, faker, TargetTypeEnum.alertgroup, alertgroup.id, TargetTypeEnum.alert, alert.id)

    db_obj = crud.link.delete_links(db, TargetTypeEnum.alertgroup, alertgroup.id, TargetTypeEnum.alert, alert.id, False)

    assert len(db_obj) == 1
    assert db_obj[0].id == link1.id

    db_obj = crud.link.delete_links(db, TargetTypeEnum.alert, alert.id, TargetTypeEnum.alertgroup, alertgroup.id, False)

    assert len(db_obj) == 1
    assert db_obj[0].id == link2.id


def test_delete_links_for_objects(db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    link = create_link(db, faker, TargetTypeEnum.alert, alert.id)

    db_obj = crud.link.delete_links_for_object(db, TargetTypeEnum.none, -1)

    assert db_obj is None

    db_obj = crud.link.delete_links_for_object(db, TargetTypeEnum.alert, alert.id)

    assert len(db_obj) == 1

    link_obj = crud.link.get(db, link.id)

    assert link_obj is None
