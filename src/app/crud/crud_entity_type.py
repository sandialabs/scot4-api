from app.crud.base import CRUDBase
from app.models.entity_type import EntityType
from app.schemas.entity_type import EntityTypeCreate, EntityTypeUpdate


class CRUDEntityType(CRUDBase[EntityType, EntityTypeCreate, EntityTypeUpdate]):
    pass


entity_type = CRUDEntityType(EntityType)
