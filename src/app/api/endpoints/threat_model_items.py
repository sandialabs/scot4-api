from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import (
    generic_delete,
    generic_get,
    generic_post,
    generic_put,
    generic_source_add_remove,
    generic_tag_untag,
    generic_search
)

router = APIRouter()


# Create get, post, put, delete, entries, tag, and source endpoints
generic_get(
    router,
    crud.threat_model_item,
    TargetTypeEnum.threat_model_item,
    schemas.ThreatModelItem,
)
generic_post(
    router,
    crud.threat_model_item,
    TargetTypeEnum.threat_model_item,
    schemas.ThreatModelItem,
    schemas.ThreatModelItemCreate,
)
generic_put(
    router,
    crud.threat_model_item,
    TargetTypeEnum.threat_model_item,
    schemas.ThreatModelItem,
    schemas.ThreatModelItemUpdate,
)
generic_delete(
    router,
    crud.threat_model_item,
    TargetTypeEnum.threat_model_item,
    schemas.ThreatModelItem,
)
generic_tag_untag(
    router,
    crud.threat_model_item,
    TargetTypeEnum.threat_model_item,
    schemas.ThreatModelItem,
)
generic_source_add_remove(
    router,
    crud.threat_model_item,
    TargetTypeEnum.threat_model_item,
    schemas.ThreatModelItem,
)
generic_search(router, crud.threat_model_item, TargetTypeEnum.threat_model_item, schemas.ThreatModelItemSearch, schemas.ThreatModelItem)
