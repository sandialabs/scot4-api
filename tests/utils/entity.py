import random
from faker import Faker
from sqlalchemy.orm import Session

from app import crud
from app.enums import EntityStatusEnum, TargetTypeEnum, EnrichmentClassEnum
from app.schemas.entity import EntityCreate
from app.schemas.link import LinkCreate
from app.schemas.enrichment import EnrichmentCreate

try:
    from tests.utils.entity_class import create_random_entity_class
    from tests.utils.entity_type import create_random_entity_type
    from tests.utils.pivot import create_random_pivot
except ImportError:
    # needed to make initial_data.py function properly
    from entity_class import create_random_entity_class
    from entity_type import create_random_entity_type
    from pivot import create_random_pivot


def create_random_entity(db: Session, faker: Faker, target_type_enum: TargetTypeEnum | None = None, target_type_id: int = 0, entity_type_id: int | None = None, entity_class_ids: list[int] = None, enrich: bool = False, pivot: bool = True):
    if entity_type_id is None:
        entity_type_id = create_random_entity_type(db, faker).id

    if pivot:
        create_random_pivot(db, faker, [entity_type_id])

    entity_create = EntityCreate(
        classes=[],
        entity_count=faker.pyint(1, 20),
        status=random.choice(list(EntityStatusEnum)),
        value=faker.word(),
        data_ver=str(faker.pyfloat(1, 1, True)),
        type_id=entity_type_id
    )

    entity = crud.entity.create(db, obj_in=entity_create)
    if entity_class_ids is None:
        entity_class_ids = [create_random_entity_class(db, faker).id for _ in range(2)]
    crud.entity.add_entity_classes(db, entity.id, entity_class_ids)

    if enrich:
        enrichment = EnrichmentCreate(
            title=faker.word(),
            entity_id=entity.id,
            enrichment_class=random.choice(list(EnrichmentClassEnum)),
            data=faker.pydict(value_types=(str, int, float, bool)),
            description=faker.sentence()
        )
        crud.enrichment.create(db, obj_in=enrichment)

    if target_type_enum is not None:
        link_create = LinkCreate(
            v1_type=TargetTypeEnum.entity,
            v1_id=entity.id,
            v0_type=target_type_enum,
            v0_id=target_type_id
        )
        crud.link.create(db, obj_in=link_create)

    return entity


def create_entity(value: str, type_name: str):
    status = EntityStatusEnum.tracked
    value = value
    type_name = type_name

    entity_create = EntityCreate(
        status=status, value=value, type_name=type_name, data_ver="0"
    )

    return entity_create
