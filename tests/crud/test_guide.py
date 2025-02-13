import random
from faker import Faker
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum, GuideStatusEnum
from app.models import Guide
from app.schemas.guide import GuideCreate, GuideUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.guide import create_random_guide
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role
from tests.utils.signature import create_random_signature
from tests.utils.permission import create_random_permission


def test_get_guide(db: Session, faker: Faker) -> None:
    guide = create_random_guide(db, faker)
    db_obj = crud.guide.get(db, guide.id)

    assert db_obj.id == guide.id

    db_obj = crud.guide.get(db, -1)

    assert db_obj is None


def test_get_multi_guide(db: Session, faker: Faker) -> None:
    guides = []
    for _ in range(5):
        guides.append(create_random_guide(db, faker))

    db_objs = crud.guide.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == guides[0].id for i in db_objs)

    db_objs = crud.guide.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == guides[1].id for i in db_objs)

    db_objs = crud.guide.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.guide.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_guide(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    guide = GuideCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence(),
        status=random.choice(list(GuideStatusEnum)),
        application=jsonable_encoder(faker.pydict()),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
    )
    db_obj = crud.guide.create(db, obj_in=guide)

    assert db_obj.id is not None
    assert db_obj.owner == guide.owner
    assert db_obj.tlp == guide.tlp
    assert db_obj.subject == guide.subject
    assert db_obj.status == guide.status
    assert db_obj.application == guide.application
    assert db_obj.data_ver == guide.data_ver
    assert db_obj.data == guide.data


def test_update_guide(db: Session, faker: Faker) -> None:
    guide = create_random_guide(db, faker)
    owner = create_random_user(db, faker)
    update = GuideUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence(),
        status=random.choice(list(GuideStatusEnum)),
        application=jsonable_encoder(faker.pydict()),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
    )

    db_obj = crud.guide.update(db, db_obj=guide, obj_in=update)

    assert db_obj.id == guide.id
    assert db_obj.owner == update.owner
    assert db_obj.tlp == update.tlp
    assert db_obj.subject == update.subject
    assert db_obj.status == update.status
    assert db_obj.application == update.application
    assert db_obj.data_ver == update.data_ver

    update = {}

    db_obj = crud.guide.update(db, db_obj=guide, obj_in=update)

    assert db_obj.id == guide.id

    update = {
        "test": "test"
    }

    db_obj = crud.guide.update(db, db_obj=guide, obj_in=update)

    assert db_obj.id == guide.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "subject": faker.sentence(),
        "status": random.choice(list(GuideStatusEnum)),
        "application": jsonable_encoder(faker.pydict()),
        "data_ver": str(faker.pyfloat(1, 1, True)),
        "data": jsonable_encoder(faker.pydict()),
    }

    db_obj = crud.guide.update(db, db_obj=Guide(), obj_in=update)

    assert db_obj.id == guide.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.subject == update["subject"]
    assert db_obj.status == update["status"]
    assert db_obj.application == update["application"]
    assert db_obj.data_ver == update["data_ver"]
    assert db_obj.data == update["data"]


def test_remove_guide(db: Session, faker: Faker) -> None:
    guide = create_random_guide(db, faker)

    db_obj = crud.guide.remove(db, _id=guide.id)

    assert db_obj.id == guide.id

    db_obj_del = crud.guide.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.guide.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_guide(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    guide = GuideCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence(),
        status=random.choice(list(GuideStatusEnum)),
        application=jsonable_encoder(faker.pydict()),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
    )

    db_obj = crud.guide.get_or_create(db, obj_in=guide)

    assert db_obj.id is not None

    same_db_obj = crud.guide.get_or_create(db, obj_in=guide)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_guide(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    guides = []
    for _ in range(5):
        guides.append(create_random_guide(db, faker, owner))

    random_guide = random.choice(guides)

    db_obj, count = crud.guide.query_with_filters(db, filter_dict={"id": random_guide.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_guide.id

    db_obj, count = crud.guide.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(guides)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.guide.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(guides) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.guide.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.guide.query_with_filters(db, filter_dict={"subject": random_guide.subject})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0].id == random_guide.id

    db_obj, count = crud.guide.query_with_filters(db, filter_dict={"subject": f"!{random_guide.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_guide.subject for a in db_obj)


def test_get_with_roles_guide(db: Session, faker: Faker) -> None:
    guides = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        guide = GuideCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            subject=faker.sentence(),
            status=random.choice(list(GuideStatusEnum)),
            application=jsonable_encoder(faker.pydict()),
            data_ver=str(faker.pyfloat(1, 1, True)),
            data=jsonable_encoder(faker.pydict()),
        )
        roles.append(role)

        guides.append(crud.guide.create_with_permissions(db, obj_in=guide, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.guide.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_guide(db: Session, faker: Faker) -> None:
    guides = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        guide = GuideCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            subject=faker.sentence(),
            status=random.choice(list(GuideStatusEnum)),
            application=jsonable_encoder(faker.pydict()),
            data_ver=str(faker.pyfloat(1, 1, True)),
            data=jsonable_encoder(faker.pydict()),
        )
        roles.append(role)

        guides.append(crud.guide.create_with_permissions(db, obj_in=guide, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.guide.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_guide(db: Session, faker: Faker) -> None:
    guide = GuideCreate(
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence(),
        status=random.choice(list(GuideStatusEnum)),
        application=jsonable_encoder(faker.pydict()),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.guide.create_with_owner(db, obj_in=guide, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == guide.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_guide(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    guide = GuideCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence(),
        status=random.choice(list(GuideStatusEnum)),
        application=jsonable_encoder(faker.pydict()),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
    )

    db_obj = crud.guide.create_with_permissions(db, obj_in=guide, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == guide.owner
    assert db_obj.tlp == guide.tlp
    assert db_obj.subject == guide.subject
    assert db_obj.status == guide.status
    assert db_obj.application == guide.application
    assert db_obj.data_ver == guide.data_ver

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.guide, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_guide(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    guide = GuideCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence(),
        status=random.choice(list(GuideStatusEnum)),
        application=jsonable_encoder(faker.pydict()),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.guide.create_in_object(db, obj_in=guide, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == guide.subject

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v0_type": TargetTypeEnum.alertgroup, "v1_id": db_obj.id, "v1_type": TargetTypeEnum.guide})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_guide(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    guide = GuideCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence(),
        status=random.choice(list(GuideStatusEnum)),
        application=jsonable_encoder(faker.pydict()),
        data_ver=str(faker.pyfloat(1, 1, True)),
        data=jsonable_encoder(faker.pydict()),
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.guide.create(db, obj_in=guide, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.guide.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_guide(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    guide = create_random_guide(db, faker, user)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.guide.remove(db, _id=guide.id, audit_logger=audit_logger)

    assert db_obj.id == guide.id

    db_obj = crud.guide.undelete(db, db_obj.id)

    assert db_obj is None


def test_get_signatures_for_guide(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    user = create_user_with_role(db, role, faker)
    signature = create_random_signature(db, faker, user)
    guide = create_random_guide(db, faker, user, signature, False)
    create_random_permission(db, role, guide)

    db_obj = crud.guide.get_signatures_for(db, guide.id)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0].id == signature.id

    bad_role = create_random_role(db, faker)
    db_obj = crud.guide.get_signatures_for(db, guide.id, [bad_role])

    assert db_obj is not None
    assert len(db_obj) == 0
