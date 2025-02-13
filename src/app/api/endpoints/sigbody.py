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
    generic_undelete,
    generic_search
)

router = APIRouter()

# Create get, post, put, delete, tag, and source endpoints
generic_get(router, crud.sigbody, TargetTypeEnum.sigbody, schemas.Sigbody, "Signature Body")
generic_post(router, crud.sigbody, TargetTypeEnum.sigbody, schemas.Sigbody, schemas.SigbodyCreate, "Signature Body")
generic_put(router, crud.sigbody, TargetTypeEnum.sigbody, schemas.Sigbody, schemas.SigbodyUpdate, "Signature Body")
generic_delete(router, crud.sigbody, TargetTypeEnum.sigbody, schemas.Sigbody, "Signature Body")
generic_undelete(router, crud.sigbody, TargetTypeEnum.sigbody, schemas.Sigbody, "Signature Body")
generic_tag_untag(router, crud.sigbody, TargetTypeEnum.sigbody, schemas.Sigbody, "Signature Body")
generic_source_add_remove(router, crud.sigbody, TargetTypeEnum.sigbody, schemas.Sigbody, "Signature Body")
generic_search(router, crud.sigbody, TargetTypeEnum.sigbody, schemas.SigbodySearch, schemas.Sigbody, "Signature Body")
