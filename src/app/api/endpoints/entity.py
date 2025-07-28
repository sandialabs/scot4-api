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
    generic_export,
    generic_upvote_and_downvote,
    generic_user_links
)

router = APIRouter()


generic_get(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_put(router, crud.entity, TargetTypeEnum.entity, schemas.Entity, schemas.EntityUpdate)
generic_delete(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_search(router, crud.entity, TargetTypeEnum.entity, schemas.EntitySearch, schemas.Entity)
generic_undelete(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_entries(router, TargetTypeEnum.entity)
generic_tag_untag(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_source_add_remove(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_entities(router, TargetTypeEnum.entity)
generic_history(router, crud.entity, TargetTypeEnum.entity)
generic_export(router, crud.entity, TargetTypeEnum.entity)
generic_upvote_and_downvote(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)
generic_user_links(router, crud.entity, TargetTypeEnum.entity, schemas.Entity)


description, _ = create_schema_details(FlairResults,
    "Used by the flair engine to add flair results")


@router.post("/flair/results", description=description)
def add_flair_results(
    obj: Annotated[FlairResults, Body(...)],
    db: Session = Depends(deps.get_db),
    _: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    crud.entity.add_flair_results(db, obj, audit_logger)


description, examples = create_schema_details(EntityCreate,
    "Create an entity, optionally linking it to an existing item. "
    "You can also specify a whether the flair engine should search "
    "for this entity when flairing new items.")
many_description, many_examples = create_schema_details(EntityCreate,
    "Create multiple entities, optionally linking them to an existing item. "
    "You can also specify a whether the flair engine should search for these "
    "entities when flairing new items.")
for example in many_examples:
    many_examples[example]["value"] = [many_examples[example]["value"]]


@router.post("/many", response_model=list[schemas.Entity], summary="Create many entities", description=many_description)
def add_entity(
    entities: Annotated[list[EntityCreate], Body(openapi_examples=many_examples)],
    create_flair_regex: Annotated[bool | None, Body(...)] = False,
    target_type: Annotated[TargetTypeEnum | None, Body(...)] = TargetTypeEnum.none,
    target_id: Annotated[int | None, Body(...)] = None,
    db: Session = Depends(deps.get_db),
    roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    _obj = []
    for entity in entities:
        _obj.append(add_entity(entity, create_flair_regex, target_type, target_id, db, roles, audit_logger))
    return _obj


@router.post("/", response_model=schemas.Entity, summary="Create an entity", description=description)
def add_entity(
    entity: Annotated[EntityCreate, Body(..., openapi_examples=examples)],
    create_flair_regex: Annotated[bool | None, Body(...)] = False,
    target_type: Annotated[TargetTypeEnum | None, Body(...)] = TargetTypeEnum.none,
    target_id: Annotated[int | None, Body(...)] = None,
    db: Session = Depends(deps.get_db),
    _: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    # Check if the entity Type exists
    _entity_type = crud.entity_type.get_or_create(db, EntityTypeCreate(name=entity.type_name), audit_logger)
    _entity = crud.entity.get_or_create(db, entity, audit_logger)
    # We've created or otherwise retrieved the entity, now we need to link it and add the appearance.
    if target_type is not None and target_id is not None:
        crud.entity.link_entity(db, _entity.id, target_type, target_id, "entity", audit_logger)

    # If the create_flair_regex is set to True, proxy a request to the flair engine endpoint to create a new regex for this entity
    if create_flair_regex:
        send_new_regex_request(_entity.value, _entity_type.name)
    return _entity


@router.get(
    "/{id}/flair_appearances",
    response_model=schemas.EntityAppearancesForFlair,
    dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.entity, PermissionEnum.read))],
    summary="Get entity appearances"
)
def entity_appearances_for_flair(
    id: Annotated[int, Path(...)],
    skip: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = 10,
    db: Session = Depends(deps.get_db),
):
    """
    Get a list of all appearances of this particular entity across all flairable items.
    The pagination parameters apply to each type of item individually.
    """
    return crud.entity.retrieve_entity_links_for_flair_pane(db, id, skip, limit)


@router.get(
    "/{id}/pivot",
    response_model=schemas.ListResponse[Pivot],
    dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.entity, PermissionEnum.read))],
    summary="Get pivots for entity"
)
def entity_pivots(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    _: list[models.Role] = Depends(deps.get_current_roles),
):
    """
    Get a list of all pivots that should be displayed for an entity
    """
    _pivots, count = crud.entity.retrieve_entity_pivots(db, id)
    return {"totalCount": count, "resultCount": len(_pivots), "result": _pivots}


@router.get(
    "/{id}/enrichment",
    response_model=dict[str, list[schemas.Enrichment]],
    dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.entity, PermissionEnum.read))],
    summary="Get enrichments for entity"
)
def entity_enrichments(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    _: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Get a list of all enrichments attached to an entity
    """
    _entity = crud.entity.get(db, id, audit_logger)
    if not _entity:
        raise HTTPException(404, f"Entity {id} not found")

    return _entity.available_enrichments


description, examples = create_schema_details(schemas.entity_class.EntityClassLink,
    "Add one or more entity classes to an entity, either by name or by id")


@router.post(
    "/{id}/entity_class",
    response_model=schemas.Entity,
    dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.entity, PermissionEnum.read))],
    description=description,
    summary="Add entity class"
)
def add_entity_class(
    id: Annotated[int, Path(...)],
    entity_classes: Annotated[schemas.entity_class.EntityClassLink, Body(...)],
    db: Session = Depends(deps.get_db),
    _: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    entity = crud.entity.add_entity_classes(db, id, entity_classes.entity_class_ids, audit_logger)
    if entity is None:
        raise HTTPException(404, f"Entity {id} not found")

    return entity


@router.post(
    "/{id}/enrichment",
    response_model=schemas.Entity,
    dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.entity, PermissionEnum.read))],
    summary="Add enrichment to entity"
)
def add_enrichment(
    id: Annotated[int, Path(...)],
    enrichment: schemas.EnrichmentCreate,
    db: Session = Depends(deps.get_db),
    _: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Add an enrichment to an entity
    """
    data_schema = enrichment_class_schema_map[enrichment.enrichment_class]
    try:
        data_schema(**enrichment.data)
    except ValidationError as e:
        raise HTTPException(422, str(e))
    entity = crud.entity.add_enrichment(
        db_session=db, entity_id=id, enrichment=enrichment, audit_logger=audit_logger
    )
    if entity is None:
        raise HTTPException(404, f"Entity {id} not found")
    return entity


remove_examples = {
    "basic": {"summary": "Basic Example", "value": {"entity_class_ids": [1, 2]}}
}


@router.post(
    "/{id}/entity_class/remove",
    response_model=schemas.Entity,
    dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.entity, PermissionEnum.read))],
    summary="Remove entity class"
)
def remove_entity_class(
    id: Annotated[int, Path(...)],
    body: Annotated[dict[str, list[int]], Body(openapi_examples=remove_examples)],
    db: Session = Depends(deps.get_db),
    _: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
):
    """
    Remove one or more entity classes from an entity by id
    """
    entity_class_ids = body.get("entity_class_ids")
    if not entity_class_ids:
        raise HTTPException(422, "You must specify entity_class_ids")

    entity = crud.entity.remove_entity_classes(db, id, entity_class_ids, audit_logger)
    if entity is None:
        raise HTTPException(404, f"Entity {id} not found")
    return entity


@router.post("/{id}/enrich_request", summary="Enrich an entity")
def enrich_entity(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
):
    """
    Requests the enricher to re-enrich an existing entity
    """
    entity = crud.entity.get(db, id)
    if entity is None:
        raise HTTPException(404, f"Entity {id} not found")

    send_flair_enrichment_request(entity)
    return {"message": "Enrichment queued"}
