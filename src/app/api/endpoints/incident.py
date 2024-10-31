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
generic_export(router, crud.incident, TargetTypeEnum.incident)
generic_get(router, crud.incident, TargetTypeEnum.incident, schemas.Incident)
generic_post(
    router,
    crud.incident,
    TargetTypeEnum.incident,
    schemas.Incident,
    schemas.IncidentCreate,
)
generic_put(
    router,
    crud.incident,
    TargetTypeEnum.incident,
    schemas.Incident,
    schemas.IncidentUpdate,
)
generic_delete(router, crud.incident, TargetTypeEnum.incident, schemas.Incident)
generic_undelete(router, crud.incident, TargetTypeEnum.incident, schemas.Incident)
generic_entries(router, TargetTypeEnum.incident)
generic_tag_untag(router, crud.incident, TargetTypeEnum.incident, schemas.Incident)
generic_source_add_remove(
    router, crud.incident, TargetTypeEnum.incident, schemas.Incident
)
generic_entities(router, TargetTypeEnum.incident)
generic_history(router, crud.incident, TargetTypeEnum.incident)
generic_files(router, TargetTypeEnum.incident)
generic_search(router, crud.incident, TargetTypeEnum.incident, schemas.IncidentSearch, schemas.Incident)
