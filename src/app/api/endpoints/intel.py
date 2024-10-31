from fastapi import APIRouter

from app import crud, schemas
from app.enums import TargetTypeEnum

from .generic import (
    generic_delete,
    generic_entities,
    generic_entries,
    generic_get,
    generic_post,
    generic_put,
    generic_source_add_remove,
    generic_tag_untag,
    generic_undelete,
    generic_history,
    generic_files,
    generic_search,
    generic_export
)

router = APIRouter()

# Create get, post, put, delete, entries, tag, and source endpoints
generic_export(router, crud.intel, TargetTypeEnum.intel)
generic_get(router, crud.intel, TargetTypeEnum.intel, schemas.Intel)
generic_post(
    router, crud.intel, TargetTypeEnum.intel, schemas.Intel, schemas.IntelCreate
)
generic_put(
    router, crud.intel, TargetTypeEnum.intel, schemas.Intel, schemas.IntelUpdate
)
generic_delete(router, crud.intel, TargetTypeEnum.intel, schemas.Intel)
generic_undelete(router, crud.intel, TargetTypeEnum.intel, schemas.Intel)
generic_entries(router, TargetTypeEnum.intel)
generic_tag_untag(router, crud.intel, TargetTypeEnum.intel, schemas.Intel)
generic_source_add_remove(router, crud.intel, TargetTypeEnum.intel, schemas.Intel)
generic_entities(router, TargetTypeEnum.intel)
generic_history(router, crud.intel, TargetTypeEnum.intel)
generic_files(router, TargetTypeEnum.intel)
generic_search(router, crud.intel, TargetTypeEnum.intel, schemas.IntelSearch, schemas.Intel)
