from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import generic_post, generic_put, generic_get, generic_history, generic_search, generic_export

router = APIRouter()

# Create get, post, put, and delete endpoints
generic_get(router, crud.entity_class, TargetTypeEnum.entity_class, schemas.EntityClass)
generic_post(router, crud.entity_class, TargetTypeEnum.entity_class, schemas.EntityClass, schemas.EntityClassCreate, permissions=False)
generic_put(router, crud.entity_class, TargetTypeEnum.entity_class, schemas.EntityClass, schemas.EntityClassUpdate)
generic_search(router, crud.entity_class, TargetTypeEnum.entity_class, schemas.EntityClassSearch, schemas.EntityClass)
generic_history(router, crud.entity_class, TargetTypeEnum.entity_class)
generic_export(router, crud.entity_class, TargetTypeEnum.entity_class)
