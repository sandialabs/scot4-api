from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import generic_post, generic_put, generic_get, generic_search

router = APIRouter()

# Create get, post, put, and delete endpoints

generic_post(router, crud.entity_type, TargetTypeEnum.entity_type, schemas.EntityType, schemas.EntityTypeCreate)
generic_put(router, crud.entity_type, TargetTypeEnum.entity_type, schemas.EntityType, schemas.EntityTypeUpdate)
generic_get(router, crud.entity_type, TargetTypeEnum.entity_type, schemas.EntityType)
generic_search(router, crud.entity_type, TargetTypeEnum.entity_type, schemas.EntityTypeSearch, schemas.EntityType)
