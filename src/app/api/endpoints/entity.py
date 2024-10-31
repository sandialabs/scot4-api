from pydantic import ValidationError
from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum
from app.schemas.entity import EntityCreate
from app.schemas.entity_type import EntityTypeCreate
from app.schemas.pivot import Pivot
from app.schemas.flair import FlairResults
from app.schemas import enrichment_class_schema_map
from app.utils import send_flair_enrichment_request, send_new_regex_request, create_schema_details

from .generic import (
    generic_delete,
    generic_entities,
    generic_entries,
    generic_get,
    generic_put,
    generic_source_add_remove,
    generic_tag_untag,
    generic_undelete,
    generic_history,
    generic_search,
    generic_export
)

router = APIRouter()
description, examples = create_schema_details(FlairResults)
description_entity_create, examples_entity_create = create_schema_details(EntityCreate)
description_entity_link, examples_entity_link = create_schema_details(schemas.entity_class.EntityClassLink)


# Create get, post, put, and delete endpoints
generic_export(router, crud.entity, TargetTypeEnum.entity)
generic_get(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_put(
    router, crud.entity, TargetTypeEnum.entity, schemas.Entity, schemas.EntityUpdate
)
generic_delete(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_undelete(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
# Tag, source, and entry endpoints
generic_entries(router, TargetTypeEnum.entity)
generic_tag_untag(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_source_add_remove(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_entities(router, TargetTypeEnum.entity)
generic_history(router, crud.entity, TargetTypeEnum.entity)
generic_search(router, crud.entity, TargetTypeEnum.entity, schemas.EntitySearch, schemas.Entity)


@router.post("/flair/results", description=description)
def add_flair_results(
    obj: Annotated[FlairResults, Body(..., openapi_examples=examples)],
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    crud.entity.add_flair_results(db_session=db, flair_results=obj, audit_logger=audit_logger)


@router.post(
    "/", response_model=schemas.Entity, dependencies=[], description=description_entity_create
)
def add_entity(
    entity: Annotated[EntityCreate, Body(..., openapi_examples=examples_entity_create)],
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    create_flair_regex: Annotated[bool | None, Body(...)] = False,
    target_type: Annotated[TargetTypeEnum | None, Body(...)] = TargetTypeEnum.none,
    target_id: Annotated[int | None, Body(...)] = None,
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):

    # Check if the entity Type exists
    entity_type = EntityTypeCreate(name=entity.type_name)
    _entity_type = crud.entity_type.get_or_create(db_session=db, obj_in=entity_type, audit_logger=audit_logger)
    _entity = crud.entity.get_or_create(
        db_session=db, obj_in=entity, audit_logger=audit_logger
    )
    # We've created or otherwise retrieved the entity, now we need to link it and add the appearance.
    if target_type is not None and target_id is not None:
        crud.entity.link_entity(
            db_session=db,
            entity_id=_entity.id,
            target_type=target_type,
            target_id=target_id,
            context="entity",
            audit_logger=audit_logger,
        )

    # If the create_flair_regex is set to True, proxy a request to the flair engine endpoint to create a new regex for this entity
    if create_flair_regex:
        send_new_regex_request(_entity.value, _entity_type.name)
    return _entity


entity_read_dep = Depends(
    deps.PermissionCheckId(TargetTypeEnum.entity, PermissionEnum.read)
)


@router.get(
    "/{id}/flair_appearances",
    response_model=schemas.EntityAppearancesForFlair,
    dependencies=[entity_read_dep],

)
def entity_appearances_for_flair(
    id: Annotated[int, Path(...)],
    skip: Annotated[int | None, Query(...)] = 0,
    limit: Annotated[int | None, Query(...)] = 10,
    db: Session = Depends(deps.get_db),
):
    appearances_for_flair = crud.entity.retrieve_entity_links_for_flair_pane(db, id, skip, limit)
    return appearances_for_flair


@router.get(
    "/{id}/pivot",
    response_model=schemas.ListResponse[Pivot],
    dependencies=[entity_read_dep],
)
def entity_pivots(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
):
    _pivots, count = crud.entity.retrieve_entity_pivots(
        db_session=db, entity_id=id
    )
    return {"totalCount": count, "resultCount": len(_pivots), "result": _pivots}


@router.get(
    "/{id}/enrichment",
    response_model=dict[str, list[schemas.Enrichment]],
    dependencies=[entity_read_dep],
)
def entity_enrichments(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    _entity = crud.entity.get(db_session=db, _id=id, audit_logger=audit_logger)
    if not _entity:
        raise HTTPException(404, f"Entity {id} not found")

    return _entity.available_enrichments


@router.post(
    "/{id}/entity_class", response_model=schemas.Entity, dependencies=[entity_read_dep], description=description_entity_link
)
def add_entity_class(
    id: Annotated[int, Path(...)],
    entity_classes: Annotated[schemas.entity_class.EntityClassLink, Body(..., openapi_examples=examples_entity_link)],
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):

    entity = crud.entity.add_entity_classes(
        db_session=db,
        entity_id=id,
        entity_classes=entity_classes.entity_class_ids,
        audit_logger=audit_logger
    )
    if entity is None:
        raise HTTPException(404, f"Entity {id} not found")

    return entity


@router.post(
    "/{id}/enrichment", response_model=schemas.Entity, dependencies=[entity_read_dep]
)
def add_enrichment(
    id: Annotated[int, Path(...)],
    enrichment: schemas.EnrichmentCreate,
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
):

    # Validate Enrichment by type
    data_schema = enrichment_class_schema_map[enrichment.enrichment_class]
    try:
        data_schema(**enrichment.data)
    except ValidationError as e:
        raise HTTPException(422, str(e))
    entity = crud.entity.add_enrichment(
        db_session=db, entity_id=id, enrichment=enrichment
    )
    if entity is None:
        raise HTTPException(404, f"Entity {id} not found")
    return entity


@router.post(
    "/{id}/entity_class/remove",
    response_model=schemas.Entity,
    dependencies=[entity_read_dep],
)
def remove_entity_class(
    id: Annotated[int, Path(...)],
    body: Annotated[dict[str, list[int]], Body(...)],
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    entity_class_ids = body.get("entity_class_ids")
    if not entity_class_ids:
        raise HTTPException(422, "You must specify entity_class_ids")

    entity = crud.entity.remove_entity_classes(
        db_session=db,
        entity_id=id,
        entity_classes=entity_class_ids,
        audit_logger=audit_logger
    )
    if entity is None:
        raise HTTPException(404, f"Entity {id} not found")
    return entity


@router.post("/{id}/enrich_request", summary="Enrich an entity")
def enrich_entity(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    user: models.User = Depends(deps.get_current_active_user),
):
    """
    Requests the enricher to re-enrich an existing entity
    """
    entity = crud.entity.get(db, id)
    if entity is None:
        raise HTTPException(404, f"Entity {id} not found")

    send_flair_enrichment_request(entity)
    return {"message": "Enrichment queued"}
