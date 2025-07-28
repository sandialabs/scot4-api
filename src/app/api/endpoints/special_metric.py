from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import (
    generic_delete,
    generic_get,
    generic_post,
    generic_put,
    generic_undelete,
    generic_history,
    generic_search,
)

router = APIRouter()

# Create get, post, put, delete, entries, tag, and source endpoints
generic_get(router, crud.special_metric, TargetTypeEnum.special_metric, schemas.SpecialMetric)
generic_post(router, crud.special_metric, TargetTypeEnum.special_metric, schemas.SpecialMetric, schemas.SpecialMetricCreate, permissions=False, admin_only=True)
generic_put(router, crud.special_metric, TargetTypeEnum.special_metric, schemas.SpecialMetric, schemas.SpecialMetricUpdate, admin_only=True)
generic_delete(router, crud.special_metric, TargetTypeEnum.special_metric, schemas.SpecialMetric, admin_only=True)
generic_search(router, crud.special_metric, TargetTypeEnum.special_metric, schemas.SpecialMetricSearch, schemas.SpecialMetric)
generic_undelete(router, crud.special_metric, TargetTypeEnum.special_metric, schemas.SpecialMetric)
generic_history(router, crud.special_metric, TargetTypeEnum.special_metric)
