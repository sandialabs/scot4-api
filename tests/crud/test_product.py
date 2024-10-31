import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.api.deps import AuditLogger
from app.enums import TlpEnum, PermissionEnum, TargetTypeEnum
from app.models import Product
from app.schemas.product import ProductCreate, ProductUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.product import create_random_product
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user, create_user_with_role


def test_get_product(db: Session, faker: Faker) -> None:
    product = create_random_product(db, faker, create_extras=False)
    db_obj = crud.product.get(db, product.id)

    assert db_obj.id == product.id

    db_obj = crud.product.get(db, -1)

    assert db_obj is None


def test_get_multi_product(db: Session, faker: Faker) -> None:
    products = []
    for _ in range(5):
        products.append(create_random_product(db, faker, create_extras=False))

    db_objs = crud.product.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == products[0].id for i in db_objs)

    db_objs = crud.product.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == products[1].id for i in db_objs)

    db_objs = crud.product.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.product.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_product(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    product = ProductCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence()
    )
    db_obj = crud.product.create(db, obj_in=product)

    assert db_obj.id is not None
    assert db_obj.owner == product.owner
    assert db_obj.tlp == product.tlp
    assert db_obj.subject == product.subject


def test_update_product(db: Session, faker: Faker) -> None:
    product = create_random_product(db, faker, create_extras=False)
    owner = create_random_user(db, faker)
    update = ProductUpdate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence()
    )

    db_obj = crud.product.update(db, db_obj=product, obj_in=update)

    assert db_obj.id == product.id
    assert db_obj.owner == update.owner
    assert db_obj.tlp == update.tlp
    assert db_obj.subject == update.subject

    update = {}

    db_obj = crud.product.update(db, db_obj=product, obj_in=update)

    assert db_obj.id == product.id

    update = {
        "test": "test"
    }

    db_obj = crud.product.update(db, db_obj=product, obj_in=update)

    assert db_obj.id == product.id
    assert not hasattr(db_obj, "test")

    owner = create_random_user(db, faker)
    update = {
        "owner": owner.username,
        "tlp": random.choice(list(TlpEnum)),
        "subject": faker.sentence()
    }

    db_obj = crud.product.update(db, db_obj=Product(), obj_in=update)

    assert db_obj.id == product.id + 1
    assert db_obj.owner == update["owner"]
    assert db_obj.tlp == update["tlp"]
    assert db_obj.subject == update["subject"]


def test_remove_product(db: Session, faker: Faker) -> None:
    product = create_random_product(db, faker, create_extras=False)

    db_obj = crud.product.remove(db, _id=product.id)

    assert db_obj.id == product.id

    db_obj_del = crud.product.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.product.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_product(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    product = ProductCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence()
    )

    db_obj = crud.product.get_or_create(db, obj_in=product)

    assert db_obj.id is not None

    same_db_obj = crud.product.get_or_create(db, obj_in=product)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_product(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    products = []
    for _ in range(5):
        products.append(create_random_product(db, faker, owner.username, create_extras=False))

    random_product = random.choice(products)

    db_obj, count = crud.product.query_with_filters(db, filter_dict={"id": random_product.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_product.id

    db_obj, count = crud.product.query_with_filters(db, filter_dict={"owner": owner.username})

    assert db_obj is not None
    assert len(db_obj) == len(products)
    assert len(db_obj) == count
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.product.query_with_filters(db, filter_dict={"owner": owner.username}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(products) - 1
    assert len(db_obj) == count - 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.product.query_with_filters(db, filter_dict={"owner": owner.username}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert all(a.owner == owner.username for a in db_obj)

    db_obj, count = crud.product.query_with_filters(db, filter_dict={"subject": random_product.subject})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert db_obj[0].id == random_product.id

    db_obj, count = crud.product.query_with_filters(db, filter_dict={"subject": f"!{random_product.subject}"})

    assert db_obj is not None
    assert all(a.subject != random_product.subject for a in db_obj)


def test_get_with_roles_product(db: Session, faker: Faker) -> None:
    products = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        product = ProductCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            subject=faker.sentence()
        )
        roles.append(role)

        products.append(crud.product.create_with_permissions(db, obj_in=product, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.product.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_product(db: Session, faker: Faker) -> None:
    products = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        owner = create_user_with_role(db, [role], faker)
        product = ProductCreate(
            owner=owner.username,
            tlp=random.choice(list(TlpEnum)),
            subject=faker.sentence()
        )
        roles.append(role)

        products.append(crud.product.create_with_permissions(db, obj_in=product, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.product.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_product(db: Session, faker: Faker) -> None:
    product = ProductCreate(
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.product.create_with_owner(db, obj_in=product, owner=owner)

    assert db_obj is not None
    assert db_obj.subject == product.subject
    assert hasattr(db_obj, "owner")
    assert db_obj.owner == owner.username


def test_create_with_permissions_product(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    owner = create_user_with_role(db, [role], faker)
    product = ProductCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence()
    )

    db_obj = crud.product.create_with_permissions(db, obj_in=product, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.owner == product.owner
    assert db_obj.tlp == product.tlp
    assert db_obj.subject == product.subject

    permission = crud.permission.get_permissions_from_roles(db, [role], TargetTypeEnum.product, db_obj.id)

    assert len(permission) == 1
    assert permission[0] == PermissionEnum.read


def test_create_in_object_product(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    product = ProductCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence()
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.product.create_in_object(db, obj_in=product, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.subject == product.subject

    link, _ = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v0_target": TargetTypeEnum.alertgroup, "v1_id": db_obj.id, "v1_target": TargetTypeEnum.product})

    assert any(i.v0_id == alert_group.id for i in link)
    assert any(i.v1_id == db_obj.id for i in link)


def test_get_history_product(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    product = ProductCreate(
        owner=owner.username,
        tlp=random.choice(list(TlpEnum)),
        subject=faker.sentence()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.product.create(db, obj_in=product, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.product.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_product(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    product = create_random_product(db, faker, user.username, create_extras=False)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.product.remove(db, _id=product.id, audit_logger=audit_logger)

    assert db_obj.id == product.id

    db_obj = crud.product.undelete(db, db_obj.id)

    assert db_obj is None
