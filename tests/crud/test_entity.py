import random
from faker import Faker
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app import crud
from app.api.deps import AuditLogger
from app.enums import PermissionEnum, TargetTypeEnum, EntityStatusEnum, EnrichmentClassEnum
from app.models import Entity
from app.schemas.entity import EntityCreate, EntityUpdate
from app.schemas.link import LinkCreate
from app.schemas.enrichment import EnrichmentCreate

from tests.utils.alert import create_random_alert
from tests.utils.alertgroup import create_random_alertgroup_no_sig
from tests.utils.entity_class import create_random_entity_class
from tests.utils.entity_type import create_random_entity_type
from tests.utils.entity import create_random_entity
from tests.utils.roles import create_random_role
from tests.utils.user import create_random_user
from tests.utils.pivot import create_random_pivot


def test_get_entity(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker, pivot=False)
    db_obj = crud.entity.get(db, entity.id)

    assert db_obj.id == entity.id

    db_obj = crud.entity.get(db, -1)

    assert db_obj is None


def test_get_multi_entity(db: Session, faker: Faker) -> None:
    entities = []
    for _ in range(5):
        entities.append(create_random_entity(db, faker, pivot=False))

    db_objs = crud.entity.get_multi(db)
    old_length = len(db_objs)

    assert any(i.id == entities[0].id for i in db_objs)

    db_objs = crud.entity.get_multi(db, skip=1)

    assert old_length == len(db_objs) + 1
    assert any(i.id == entities[1].id for i in db_objs)

    db_objs = crud.entity.get_multi(db, limit=1)

    assert len(db_objs) == 1

    db_objs = crud.entity.get_multi(db, skip=1, limit=1)

    assert len(db_objs) == 1


def test_create_entity(db: Session, faker: Faker) -> None:
    entity = EntityCreate(
        classes=[],
        status=random.choice(list(EntityStatusEnum)),
        value=faker.word(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        type_id=create_random_entity_type(db, faker).id
    )
    db_obj = crud.entity.create(db, obj_in=entity)

    assert db_obj.id is not None
    assert db_obj.status == entity.status
    assert db_obj.value == entity.value
    assert db_obj.classes == entity.classes
    assert db_obj.type_id == entity.type_id
    assert db_obj.data_ver == entity.data_ver


def test_update_entity(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker, pivot=False)
    update = EntityUpdate(
        status=random.choice(list(EntityStatusEnum)),
        value=faker.word(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        type_id=create_random_entity_type(db, faker).id
    )

    db_obj = crud.entity.update(db, db_obj=entity, obj_in=update)

    assert db_obj.id == entity.id
    assert db_obj.status == update.status
    assert db_obj.value == update.value
    assert db_obj.type_id == update.type_id
    assert db_obj.data_ver == update.data_ver
    assert db_obj.data == update.data

    update = {}

    db_obj = crud.entity.update(db, db_obj=entity, obj_in=update)

    assert db_obj.id == entity.id

    update = {
        "test": "test"
    }

    db_obj = crud.entity.update(db, db_obj=entity, obj_in=update)

    assert db_obj.id == entity.id
    assert not hasattr(db_obj, "test")

    entity = create_random_entity(db, faker, pivot=False)
    update = {
        "status": random.choice(list(EntityStatusEnum)),
        "value": faker.sentence(),
        "classes": [create_random_entity_class(db, faker)],
        "type_name": faker.word(),
        "type_id": faker.pyint(),
        "data_ver": str(faker.pyfloat(1, 1, True)),
        "data": jsonable_encoder(faker.pydict())
    }

    db_obj = crud.entity.update(db, db_obj=Entity(), obj_in=update)

    assert db_obj.id == entity.id + 1
    assert db_obj.status == update["status"]
    assert db_obj.value == update["value"]
    assert db_obj.classes == update["classes"]
    assert db_obj.type_id == update["type_id"]
    assert db_obj.data_ver == update["data_ver"]
    assert db_obj.data == update["data"]


def test_remove_entity(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker, pivot=False)

    db_obj = crud.entity.remove(db, _id=entity.id)

    assert db_obj.id == entity.id

    db_obj_del = crud.entity.get(db, _id=db_obj.id)

    assert db_obj_del is None

    db_obj = crud.entity.remove(db, _id=-1)

    assert db_obj is None


def test_get_or_create_entity(db: Session, faker: Faker) -> None:
    entity = EntityCreate(
        classes=[],
        status=random.choice(list(EntityStatusEnum)),
        value=faker.word(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        type_id=create_random_entity_type(db, faker).id
    )
    db_obj = crud.entity.get_or_create(db, obj_in=entity)

    assert db_obj.id is not None

    same_db_obj = crud.entity.get_or_create(db, obj_in=entity)

    assert same_db_obj.id == db_obj.id


def test_query_with_filters_entity(db: Session, faker: Faker) -> None:
    entity_type = create_random_entity_type(db, faker)
    entities = []
    for _ in range(5):
        entities.append(create_random_entity(db, faker, entity_type_id=entity_type.id, pivot=False))

    random_entity = random.choice(entities)

    db_obj, count = crud.entity.query_with_filters(db, filter_dict={"id": random_entity.id})

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == count
    assert db_obj[0].id == random_entity.id

    db_obj, count = crud.entity.query_with_filters(db, filter_dict={"type_id": entity_type.id})

    assert db_obj is not None
    assert len(db_obj) == len(entities)
    assert len(db_obj) == count
    assert all(a.type_id == entity_type.id for a in db_obj)

    db_obj, count = crud.entity.query_with_filters(db, filter_dict={"type_id": entity_type.id}, skip=1)

    assert db_obj is not None
    assert len(db_obj) == len(entities) - 1
    assert len(db_obj) == count - 1
    assert all(a.type_id == entity_type.id for a in db_obj)

    db_obj, count = crud.entity.query_with_filters(db, filter_dict={"type_id": entity_type.id}, limit=1)

    assert db_obj is not None
    assert len(db_obj) == 1
    assert len(db_obj) == 1
    assert all(a.type_id == entity_type.id for a in db_obj)

    db_obj, count = crud.entity.query_with_filters(db, filter_dict={"value": f"!{random_entity.value}"})

    assert db_obj is not None
    assert all(a.value != random_entity.value for a in db_obj)


def test_get_with_roles_entity(db: Session, faker: Faker) -> None:
    entities = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        entity = EntityCreate(
            classes=[],
            status=random.choice(list(EntityStatusEnum)),
            value=faker.word(),
            data_ver=str(faker.pyfloat(1, 1, True)),
            type_id=create_random_entity_type(db, faker).id
        )
        roles.append(role)

        entities.append(crud.entity.create_with_permissions(db, obj_in=entity, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.entity.get_with_roles(db, [random_role])

    assert len(db_obj) >= 1


def test_query_objects_with_roles_entity(db: Session, faker: Faker) -> None:
    entities = []
    roles = []
    for _ in range(5):
        role = create_random_role(db, faker)
        entity = EntityCreate(
            classes=[],
            status=random.choice(list(EntityStatusEnum)),
            value=faker.word(),
            data_ver=str(faker.pyfloat(1, 1, True)),
            type_id=create_random_entity_type(db, faker).id
        )
        roles.append(role)

        entities.append(crud.entity.create_with_permissions(db, obj_in=entity, perm_in={PermissionEnum.read: [role.id]}))

    random_role = random.choice(roles)
    db_obj = crud.entity.query_objects_with_roles(db, [random_role]).all()

    assert len(db_obj) >= 1


def test_create_with_owner_entity(db: Session, faker: Faker) -> None:
    entity = EntityCreate(
        classes=[],
        status=random.choice(list(EntityStatusEnum)),
        value=faker.word(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        type_id=create_random_entity_type(db, faker).id
    )
    owner = create_random_user(db, faker)

    # doesn't really do anything just make sure we don't get back an owner field
    db_obj = crud.entity.create_with_owner(db, obj_in=entity, owner=owner)

    assert db_obj is not None
    assert db_obj.value == entity.value
    assert not hasattr(db_obj, "owner")


def test_create_with_permissions_entity(db: Session, faker: Faker) -> None:
    role = create_random_role(db, faker)
    entity = EntityCreate(
        classes=[],
        status=random.choice(list(EntityStatusEnum)),
        value=faker.word(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        type_id=create_random_entity_type(db, faker).id
    )

    db_obj = crud.entity.create_with_permissions(db, obj_in=entity, perm_in={PermissionEnum.read: [role.id]})

    assert db_obj.id is not None
    assert db_obj.status == entity.status
    assert db_obj.value == entity.value
    assert db_obj.classes == entity.classes
    assert db_obj.type_id == entity.type_id
    assert db_obj.data_ver == entity.data_ver

    # no permission could be created with appearances so nothing should be returned
    db_query, count = crud.permission.query_with_filters(db, filter_dict={"target_id": db_obj.id, "role_id": role.id})

    assert len(db_query) == 1
    assert count == 1
    assert db_query[0].target_id == db_obj.id
    assert db_query[0].role_id == role.id


def test_create_in_object_entity(db: Session, faker: Faker) -> None:
    entity = EntityCreate(
        classes=[],
        status=random.choice(list(EntityStatusEnum)),
        value=faker.word(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        type_id=create_random_entity_type(db, faker).id
    )

    alert_group = create_random_alertgroup_no_sig(db, faker, with_alerts=False)

    db_obj = crud.entity.create_in_object(db, obj_in=entity, source_type=TargetTypeEnum.alertgroup, source_id=alert_group.id)

    assert db_obj is not None
    assert db_obj.value == entity.value

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert_group.id, "v1_id": db_obj.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert_group.id
    assert link[0].v1_id == db_obj.id


def test_get_history_entity(db: Session, faker: Faker) -> None:
    owner = create_random_user(db, faker)
    entity = EntityCreate(
        classes=[],
        status=random.choice(list(EntityStatusEnum)),
        value=faker.word(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        type_id=create_random_entity_type(db, faker).id
    )
    audit_logger = AuditLogger(owner.username, faker.ipv4(), faker.user_agent(), db)
    db_obj = crud.entity.create(db, obj_in=entity, audit_logger=audit_logger)

    assert db_obj is not None

    db_history = crud.entity.get_history(db, db_obj.id)

    assert db_history == []


def test_undelete_entity(db: Session, faker: Faker) -> None:
    user = create_random_user(db, faker)
    entity = create_random_entity(db, faker, pivot=False)
    audit_logger = AuditLogger(user.username, faker.ipv4(), faker.user_agent(), db)

    db_obj = crud.entity.remove(db, _id=entity.id, audit_logger=audit_logger)

    assert db_obj.id == entity.id

    db_obj = crud.entity.undelete(db, db_obj.id)

    assert db_obj is None


def test_retrieve_element_entities(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker, pivot=False)
    entity1 = create_random_entity(db, faker, TargetTypeEnum.entity, entity.id, pivot=False)

    db_obj, count = crud.entity.retrieve_element_entities(db, entity.id, TargetTypeEnum.entity)

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].id == entity1.id

    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    entity = create_random_entity(db, faker, TargetTypeEnum.alertgroup, alertgroup.id, pivot=False)

    db_obj, count = crud.entity.retrieve_element_entities(db, alertgroup.id, TargetTypeEnum.alertgroup)

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].id == entity.id


def test_retrieve_entity_links_for_flair_pane(db: Session, faker: Faker) -> None:
    alertgroup = create_random_alertgroup_no_sig(db, faker, with_alerts=False)
    entity = create_random_entity(db, faker, TargetTypeEnum.alertgroup, alertgroup.id, pivot=False)

    db_obj = crud.entity.retrieve_entity_links_for_flair_pane(db, entity.id)

    assert "alertgroup_appearances" not in db_obj.keys()
    assert all([len(a) == 0 for a in db_obj.values()])

    entity = create_random_entity(db, faker, pivot=False)
    alerts = []
    for _ in range(11):
        alert = create_random_alert(db, faker)
        link_create = LinkCreate(
            v1_type=TargetTypeEnum.entity,
            v1_id=entity.id,
            v0_type=TargetTypeEnum.alert,
            v0_id=alert.id
        )
        crud.link.create(db, obj_in=link_create)
        alerts.append(alert)

    db_obj = crud.entity.retrieve_entity_links_for_flair_pane(db, entity.id)

    assert "alert_appearances" in db_obj.keys()
    assert len(db_obj["alert_appearances"]) == 10
    assert db_obj["alert_appearances"][0]["id"] == alerts[-1].id

    db_obj = crud.entity.retrieve_entity_links_for_flair_pane(db, entity.id, skip=10)

    assert "alert_appearances" in db_obj.keys()
    assert len(db_obj["alert_appearances"]) == 1
    assert db_obj["alert_appearances"][0]["id"] == alerts[0].id

    db_obj = crud.entity.retrieve_entity_links_for_flair_pane(db, entity.id, limit=1)

    assert "alert_appearances" in db_obj.keys()
    assert len(db_obj["alert_appearances"]) == 1
    assert db_obj["alert_appearances"][0]["id"] == alerts[-1].id

    db_obj = crud.entity.retrieve_entity_links_for_flair_pane(db, entity.id, 1, 1)

    assert "alert_appearances" in db_obj.keys()
    assert len(db_obj["alert_appearances"]) == 1
    assert db_obj["alert_appearances"][0]["id"] == alerts[-2].id


def test_retrieve_entity_pivots(db: Session, faker: Faker) -> None:
    entity = create_random_entity(db, faker, pivot=False)

    db_obj, count = crud.entity.retrieve_entity_pivots(db, entity.id)

    assert len(db_obj) == 0
    assert count == 0

    entity_type = create_random_entity_type(db, faker)
    entity = create_random_entity(db, faker, entity_type_id=entity_type.id, pivot=False)
    pivot = create_random_pivot(db, faker, [entity_type.id])

    db_obj, count = crud.entity.retrieve_entity_pivots(db, entity.id)

    assert len(db_obj) == 1
    assert count == 1
    assert db_obj[0].id == pivot.id


def test_link_entity(db: Session, faker: Faker) -> None:
    link_entity = crud.entity.link_entity(db, -1, TargetTypeEnum.alert, -1)

    assert link_entity is None

    entity = create_random_entity(db, faker)
    alert = create_random_alert(db, faker)

    link_entity = crud.entity.link_entity(db, entity.id, TargetTypeEnum.alert, alert.id)

    assert link_entity.id == entity.id

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert.id, "v1_id": entity.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert.id
    assert link[0].v1_id == entity.id

    appearance, count = crud.appearance.query_with_filters(db, filter_dict={"target_id": alert.id, "value_id": entity.id})

    assert count == 1
    assert len(appearance) == 1
    assert appearance[0].target_id == alert.id
    assert appearance[0].value_id == entity.id


def test_add_enrichment(db: Session, faker: Faker) -> None:
    enrichment = EnrichmentCreate(
        title=faker.sentence(),
        enrichment_class=random.choice(list(EnrichmentClassEnum)),
        data=jsonable_encoder(faker.pydict())
    )
    entity_enrichment = crud.entity.add_enrichment(db, -1, enrichment)

    assert entity_enrichment is None

    entity = create_random_entity(db, faker, pivot=False)

    entity_enrichment = crud.entity.add_enrichment(db, entity.id, enrichment)

    assert len(entity_enrichment.enrichments) == 1
    assert entity_enrichment.enrichments[0].title == enrichment.title

    enrichment_obj = crud.enrichment.get(db, entity_enrichment.enrichments[0].id)

    assert enrichment_obj.id == entity_enrichment.enrichments[0].id


def test_add_entity_classes(db: Session, faker: Faker) -> None:
    entity_obj = crud.entity.add_entity_classes(db, -1, [-1])

    assert entity_obj is None

    entity = create_random_entity(db, faker, entity_class_ids=[], pivot=False)
    entity_obj = crud.entity.add_entity_classes(db, entity.id, [-1])

    assert len(entity_obj.classes) == 0

    entity_class = create_random_entity_class(db, faker)
    entity_obj = crud.entity.add_entity_classes(db, entity.id, [entity_class.id])

    assert len(entity_obj.classes) == 1
    assert entity_obj.classes[0].id == entity_class.id

    class_obj = crud.entity_class.get(db, entity_class.id)

    assert class_obj.id == entity_class.id

    entity = create_random_entity(db, faker, entity_class_ids=[], pivot=False)
    class_name = faker.word()
    entity_obj = crud.entity.add_entity_classes(db, entity.id, [class_name])

    assert len(entity.classes) == 1
    assert entity.classes[0].name == class_name

    class_obj = crud.entity_class.get(db, entity.classes[0].id)

    assert class_obj.name == class_name


def test_remove_entity_classes(db: Session, faker: Faker) -> None:
    entity_obj = crud.entity.remove_entity_classes(db, -1, [-1])

    assert entity_obj is None

    entity = create_random_entity(db, faker, pivot=False)
    entity_obj = crud.entity.remove_entity_classes(db, entity.id, [-1])

    assert len(entity_obj.classes) == len(entity.classes)
    class_ids = [a.id for a in entity.classes]
    entity_obj = crud.entity.remove_entity_classes(db, entity.id, class_ids)

    class_obj = crud.entity_class.get(db, class_ids[0])

    assert class_obj is not None


def test_link_entity_by_value(db: Session, faker: Faker) -> None:
    alert = create_random_alert(db, faker)
    entity_value = faker.word()
    entity_obj = crud.entity.link_entity_by_value(db, entity_value, TargetTypeEnum.alert, alert.id)

    assert entity_obj.value == entity_value

    link, count = crud.link.query_with_filters(db, filter_dict={"v0_id": alert.id, "v1_id": entity_obj.id})

    assert count == 1
    assert len(link) == 1
    assert link[0].v0_id == alert.id
    assert link[0].v1_id == entity_obj.id

    appearance, count = crud.appearance.query_with_filters(db, filter_dict={"target_id": alert.id, "value_id": entity_obj.id})

    assert count == 1
    assert len(appearance) == 1
    assert appearance[0].target_id == alert.id
    assert appearance[0].value_id == entity_obj.id

    entity = create_random_entity(db, faker, pivot=False)
    entity_obj = crud.entity.link_entity_by_value(db, faker.word(), TargetTypeEnum.alert, alert.id, False, entity_type=entity.type_name, entity_class=[a.id for a in entity.classes])

    assert entity_obj is None

    entity_obj = crud.entity.link_entity_by_value(db, entity.value, TargetTypeEnum.alert, alert.id, False, entity_type=entity.type_name, entity_class=[a.id for a in entity.classes])

    assert entity_obj.id == entity.id
