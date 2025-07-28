import random
from faker import Faker
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum, EnrichmentClassEnum
from app.models import Enrichment
from app.schemas.enrichment import EnrichmentCreate, EnrichmentUpdate

from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.enrichment import create_random_enrichment
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user
from tests.utils.entity import create_random_entity


def test_get_enrichment(db: Session, faker: Faker) -> None:
    enrichment = create_random_enrichment(db, faker)
    db_obj = crud.enrichment.get(db, enrichment.id)

    assert db_obj.id == enrichment.id

    db_obj = crud.enrichment.get(db, -1)

    assert db_obj is None


def test_get_multi_enrichment(db: Session, faker: Faker) -> None:
    enrichments = []
    for _ in range(5):
        enrichments.append(create_random_enrichment(db, faker))

    db_objs = crud.enrichment.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == enrichments[0].id for i in db_objs)

    db_objs = crud.enrichment.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == enrichments[1].id for i in db_objs)

    db_objs = crud.enrichment.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.enrichment.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_enrichment(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker)
    enrichment = EnrichmentCreate(
        title=faker.sentence(),
        entity_id=entity.id,
        enrichment_class=random.choice(list(EnrichmentClassEnum)),
        data=jsonable_encoder(faker.pydict()),
        description=faker.sentence()
    )
    db_obj = crud.enrichment.create(db, obj_in=enrichment)

    assert db_obj.id is not None
    assert db_obj.title == enrichment.title
    assert db_obj.entity_id == enrichment.entity_id
    assert db_obj.enrichment_class == enrichment.enrichment_class
    assert db_obj.data == enrichment.data
    assert db_obj.description == enrichment.description


def test_update_enrichment(db: Session, faker: Faker) -> None:
    enrichment = create_random_enrichment(db, faker)
    entity = create_random_entity(db, faker)
    update = EnrichmentUpdate(
        title=faker.sentence(),
        entity_id=entity.id,
        enrichment_class=random.choice(list(EnrichmentClassEnum)),
        data=jsonable_encoder(faker.pydict()),
        description=faker.sentence()
    )

    db_obj = crud.enrichment.update(db, db_obj=enrichment, obj_in=update)

    assert db_obj.id == enrichment.id
    assert db_obj.title == update.title
    assert db_obj.entity_id == update.entity_id
    assert db_obj.enrichment_class == update.enrichment_class
    assert db_obj.data == update.data
    assert db_obj.description == update.description

    update = {}

    db_obj = crud.enrichment.update(db, db_obj=enrichment, obj_in=update)

    assert db_obj.id == enrichment.id

    update = {
        "test": "test"
    }

    db_obj = crud.enrichment.update(db, db_obj=enrichment, obj_in=update)

    assert db_obj.id == enrichment.id
    assert not hasattr(db_obj, "test")

    entity = create_random_entity(db, faker)
    update = {
        "title": faker.sentence(),
        "entity_id": entity.id,
        "enrichment_class": random.choice(list(EnrichmentClassEnum)),
        "data": jsonable_encoder(faker.pydict()),
        "description": faker.sentence()
    }

    db_obj = crud.enrichment.update(db, db_obj=Enrichment(), obj_in=update)

    assert db_obj.id == enrichment.id + 1
    assert db_obj.title == update["title"]
    assert db_obj.entity_id == update["entity_id"]
    assert db_obj.enrichment_class == update["enrichment_class"]
    assert db_obj.data == update["data"]
    assert db_obj.description == update["description"]


def test_remove_enrichment(db: Session, faker: Faker) -> None:
    enrichment = create_random_enrichment(db, faker)

    db_obj = crud.enrichment.remove(db, _id=enrichment.id)

    assert db_obj.id == enrichment.id

    db_obj_del = crud.enrichment.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.enrichment.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_enrichment(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker)
    enrichment = EnrichmentCreate(
        title=faker.sentence(),
        entity_id=entity.id,
        enrichment_class=random.choice(list(EnrichmentClassEnum)),
        data=jsonable_encoder(faker.pydict()),
        description=faker.sentence()
    )

    db_obj = crud.enrichment.get_or_create(db, obj_in=enrichment)

    assert db_obj.id is not None

    same_db_obj = crud.enrichment.get_or_create(db, obj_in=enrichment)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_enrichment(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker)
    enrichments = []
    for _ in range(5):
        enrichments.append(create_random_enrichment(db, faker, entity.id))

    random_enrichment = random.choice(enrichments)

    db_obj, count = crud.enrichment.query_with_filters(db, filter_dict={"id": random_enrichment.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_enrichment.id

    db_obj, count = crud.enrichment.query_with_filters(db, filter_dict={"entity_id": entity.id})

    assert db_obj is not None
    assert len(db_obj) == len(enrichments)
    assert len(db_obj) == count
    assert all(a.entity_id == entity.id for a in db_obj)

    db_obj, count = crud.enrichment.query_with_filters(db, filter_dict={"entity_id": entity.id}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(enrichments) - 1
    assert len(db_obj) == count - 1
    assert all(a.entity_id == entity.id for a in db_obj)

    db_obj, count = crud.enrichment.query_with_filters(db, filter_dict={"entity_id": entity.id}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.entity_id == entity.id for a in db_obj)

    db_obj, count = crud.enrichment.query_with_filters(db, filter_dict={"title": f"!{random_enrichment.title}"})

    assert db_obj is not None
    assert all(a.title != random_enrichment.title for a in db_obj)


def test_get_with_roles_enrichment(db: Session, faker: Faker) -> None:
    enrichments = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        entity = create_random_entity(db, faker)
        enrichment = EnrichmentCreate(
            title=faker.sentence(),
            entity_id=entity.id,
            enrichment_class=random.choice(list(EnrichmentClassEnum)),
            data=jsonable_encoder(faker.pydict()),
            description=faker.sentence()
        )
        roles.append(role)

        enrichments.append(crud.enrichment.create_with_permissions(db, obj_in=enrichment, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.enrichment.get_with_roles(db, [random_role])

    assert len(db_obj) == 0


def test_query_objects_with_roles_enrichment(db: Session, faker: Faker) -> None:
    enrichments = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        entity = create_random_entity(db, faker)
        enrichment = EnrichmentCreate(
            title=faker.sentence(),
            entity_id=entity.id,
            enrichment_class=random.choice(list(EnrichmentClassEnum)),
            data=jsonable_encoder(faker.pydict()),
            description=faker.sentence()
        )
        roles.append(role)

        enrichments.append(crud.enrichment.create_with_permissions(db, obj_in=enrichment, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.enrichment.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) == 0


def test_create_with_owner_enrichment(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker)
    enrichment = EnrichmentCreate(
        title=faker.sentence(),
        entity_id=entity.id,
        enrichment_class=random.choice(list(EnrichmentClassEnum)),
        data=jsonable_encoder(faker.pydict()),
        description=faker.sentence()
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.enrichment.create_with_owner(db, obj_in=enrichment, owner=owner)

    assert db_obj is not None
    assert db_obj.title == enrichment.title
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_enrichment(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    entity = create_random_entity(db, faker)
    enrichment = EnrichmentCreate(
        title=faker.sentence(),
        entity_id=entity.id,
        enrichment_class=random.choice(list(EnrichmentClassEnum)),
        data=jsonable_encoder(faker.pydict()),
        description=faker.sentence()
    )

    db_obj = crud.enrichment.create_with_permissions(db, obj_in=enrichment, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.title == enrichment.title
    assert db_obj.entity_id == enrichment.entity_id
    assert db_obj.enrichment_class == enrichment.enrichment_class
    assert db_obj.data == enrichment.data
    assert db_obj.description == enrichment.description

    # no permission could be created with appearances so nothing should be returned
    db_obj, count = crud.permission.query_with_filters(db, filter_dict={"target_id": db_obj.id, "role_id": role.id})

    assert db_obj == []
    assert count == 0


def test_get_history_enrichment(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entity = create_random_entity(db, faker)
    enrichment = EnrichmentCreate(
        title=faker.sentence(),
        entity_id=entity.id,
        enrichment_class=random.choice(list(EnrichmentClassEnum)),
        data=jsonable_encoder(faker.pydict()),
        description=faker.sentence()
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.enrichment.create(db, obj_in=enrichment, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.enrichment.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_enrichment(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    enrichment = create_random_enrichment(db, faker)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.enrichment.remove(db, _id=enrichment.id, audit_logger=audit_logger)

    assert db_obj.id == enrichment.id

    db_obj = crud.enrichment.undelete(db, db_obj.id)

    assert db_obj is None
