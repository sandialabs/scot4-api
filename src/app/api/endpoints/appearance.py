from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import generic_search, generic_post, generic_get, generic_put, generic_delete

router = APIRouter()

generic_get(router, crud.appearance, TargetTypeEnum.none, schemas.Appearance, "appearance")
generic_post(router, crud.appearance, TargetTypeEnum.none, schemas.Appearance, schemas.AppearanceCreate, "appearance", True, False, False)
generic_put(router, crud.appearance, TargetTypeEnum.none, schemas.Appearance, schemas.AppearanceUpdate, "appearance", True, False)
generic_delete(router, crud.appearance, TargetTypeEnum.none, schemas.Appearance, "appearance", True, False)
generic_search(router, crud.appearance, TargetTypeEnum.none, schemas.AppearanceSearch, schemas.Appearance, "appearance")
