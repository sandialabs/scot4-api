from typing import Any, Union
from hashlib import md5
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.crud.base import CRUDBase
from app.enums import TargetTypeEnum, RemoteFlairStatusEnum
from app.utils import send_flair_enrichment_request, index_for_search, send_reflair_request, create_schema_details


router = APIRouter()


description, examples = create_schema_details(schemas.FlairUpdateResult)


@router.post(
    "/flairupdate",
    response_model=Union[schemas.AlertGroupDetailed, schemas.Entry, schemas.Alert, schemas.RemoteFlair, dict],
    description=description
)
def flair_update(
    *,
    payload: Annotated[schemas.FlairUpdateResult, Body(..., openapi_examples=examples)],
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    background_tasks: BackgroundTasks
) -> Any:
    """
    Endpoint for flair updates from flair engine
    """
    if payload.target.type == TargetTypeEnum.alertgroup:
        if not payload.alerts:
            raise HTTPException(422, "You must use the alerts field to update alerts in an alertgroup")

        alertgroup = crud.alert_group.flair_update(db, payload.target.id, payload.alerts, audit_logger)
        if not alertgroup:
            raise HTTPException(404, f"Alertgroup {payload.target.id} not found")

        obj_entities, _ = crud.entity.retrieve_element_entities(db, payload.target.id, payload.target.type)
        for entity in obj_entities:
            background_tasks.add_task(send_flair_enrichment_request, entity)

        # add alert data to search index
        for alert in alertgroup.alerts:
            background_tasks.add_task(index_for_search, alertgroup.subject, alert=alert)

        return alertgroup
    elif payload.target.type == TargetTypeEnum.alert:
        raise HTTPException(422, "To update flair for an alert, update its parent alertgroup and put the alert data in the 'alerts' field")
    elif payload.target.type == TargetTypeEnum.remote_flair:
        if payload.entities is None:
            raise HTTPException(422, "You must provide entities field when updating a remote flair object")
        flair_obj = crud.remote_flair.get(db, _id=payload.target.id)
        if flair_obj is None:
            raise HTTPException(404, f"Remote Flair {payload.target.id} Not Found")

        # search for entities that already exist
        results = {}
        for entity in payload.entities:
            results[entity] = {}
            for entity_name in payload.entities[entity]:
                results[entity][entity_name] = {"id": None}
                # if an entity exists report back the id
                entity_get = db.query(models.Entity).filter(models.Entity.type_name == entity).filter(models.Entity.value == entity_name).first()
                if entity_get:
                    results[entity][entity_name]["id"] = entity_get.id

        return crud.remote_flair.update(db, db_obj=flair_obj, obj_in={"status": RemoteFlairStatusEnum.ready, "results": results}, audit_logger=audit_logger)
    else:
        if payload.entities is None or payload.text_flaired is None:
            raise HTTPException(422, "You must provide the text_flaired and entities fields when updating a non-alertgroup object")
        target_crud = CRUDBase.target_crud_mapping.get(payload.target.type)
        if target_crud and hasattr(target_crud, "flair_update"):
            obj = target_crud.flair_update(
                db,
                payload.target.id,
                payload.text_flaired,
                payload.entities,
                payload.text,
                payload.text_plain,
                audit_logger=audit_logger,
            )
            if not obj:
                raise HTTPException(404, f"{payload.target.type.value} {payload.target.id} not found")
            if payload.target.type == TargetTypeEnum.entry and obj.entry_data.get('plain_text') is not None:
                # Index/Reindex the entry text for search
                parent_crud = CRUDBase.target_crud_mapping.get(obj.target_type)
                if parent_crud is not None:
                    parent_obj = parent_crud.get(db, obj.target_id)
                    if hasattr(parent_obj, "subject"):
                        background_tasks.add_task(index_for_search, parent_obj.subject, obj)
                    elif hasattr(parent_obj, "title"):
                        background_tasks.add_task(index_for_search, parent_obj.title, obj)
                    elif hasattr(parent_obj, "value"):
                        background_tasks.add_task(index_for_search, parent_obj.value, obj)
                    elif hasattr(parent_obj, "name"):
                        background_tasks.add_task(index_for_search, parent_obj.name, obj)
            # Also redo flair enrichment for all included entities
            obj_entities, _ = crud.entity.retrieve_element_entities(db, payload.target.id, payload.target.type)
            for entity in obj_entities:
                background_tasks.add_task(send_flair_enrichment_request, entity)
            return obj
        else:
            raise HTTPException(404, f"{payload.target.type.value} objects do not support flair updates")


@router.post("/enrich/{entity_id}", response_model=schemas.Entity)
def enrich_entity(
    *,
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    entity_id: Annotated[int, Path(...)],
    classes: Annotated[list[str], Body(...)],
    enriched_data: Annotated[dict, Body(...)],
):
    """
    Endpoint for the enricher to submit flair enrichment data
    """
    # Check for entity existence
    flair_entity = crud.entity.get(db, entity_id)
    if not flair_entity:
        raise HTTPException(404, f"Entity {entity_id} not found")
    # Assign new entity classes
    new_class_ids = []
    for class_name in classes:
        entity_class = crud.entity_class.get_by_name(db, class_name)
        if entity_class and entity_class.id not in [c.id for c in flair_entity.classes]:
            new_class_ids.append(entity_class.id)
    if len(new_class_ids) > 0:
        crud.entity.add_entity_classes(db, flair_entity.id, new_class_ids)
    # Update the flair data
    new_flair_data = {}
    if flair_entity.data:
        new_flair_data.update(flair_entity.data)
    if enriched_data:
        new_flair_data.update(enriched_data)

    return crud.entity.update(db, db_obj=flair_entity, obj_in={"data": new_flair_data}, audit_logger=audit_logger)


description, examples = create_schema_details(schemas.RemoteFlairCreate, "Creates a Remote Flair Job from the browser plugin")


@router.post(
    "/remote",
    response_model=schemas.RemoteFlair,
    summary="Create a Remote Flair job",
    description=description
)
def post_remote_flair(
    *,
    db: Session = Depends(deps.get_db),
    obj: Annotated[schemas.RemoteFlairCreate, Body(..., openapi_examples=examples)],
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    background_tasks: BackgroundTasks,
):
    # check to see if html has been flaired already and ignore md5 security bandit error
    _md5 = md5(obj.html.encode("utf-8")).hexdigest()  # nosec
    _obj = crud.remote_flair.get_md5(db, _md5)

    # if we get reflair and _obj then update md5 and clear results
    if obj.status == RemoteFlairStatusEnum.reflair and _obj is not None:
        # page request for reflair set status to processing
        obj.status = RemoteFlairStatusEnum.processing
        obj.md5 = _md5
        obj.results = {}
        dict_obj = obj.model_dump()
        dict_obj.pop("html", None)
        _obj = crud.remote_flair.update(db, db_obj=_obj, obj_in=dict_obj)
        background_tasks.add_task(send_reflair_request, _obj.id, TargetTypeEnum.remote_flair, obj.html)
    # if not then flair it
    elif _obj is None:
        obj.status = RemoteFlairStatusEnum.processing
        obj.md5 = _md5
        dict_obj = obj.model_dump()
        # remove html so it doesn't get added to the db
        dict_obj.pop("html", None)
        _obj = crud.remote_flair.create(db, obj_in=dict_obj, audit_logger=audit_logger)
        background_tasks.add_task(send_reflair_request, _obj.id, TargetTypeEnum.remote_flair, obj.html)
    
    return _obj


@router.get(
    "/remote/{id}",
    response_model=schemas.RemoteFlair,
    summary="Get Remote Flair Job",
    description="Get results from a Remote Flair Job"
)
def get_remote_flair(
    *,
    db: Session = Depends(deps.get_db),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    id: Annotated[int, Path(...)],
):
    """
    Get the remote flair status
    """

    remote_flair_obj = crud.remote_flair.get(db, id, audit_logger)
    if not remote_flair_obj:
        raise HTTPException(404, "Remote Flair not found")

    return remote_flair_obj
