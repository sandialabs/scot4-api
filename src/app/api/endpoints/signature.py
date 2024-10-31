from typing import Any, Annotated
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum

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
    generic_search,
    generic_export
)

router = APIRouter()

# Create get, post, put, delete, entries, tag, and source endpoints
generic_export(router, crud.signature, TargetTypeEnum.signature)
generic_get(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_post(
    router,
    crud.signature,
    TargetTypeEnum.signature,
    schemas.Signature,
    schemas.SignatureCreate,
)
generic_put(
    router,
    crud.signature,
    TargetTypeEnum.signature,
    schemas.Signature,
    schemas.SignatureUpdate,
)
generic_delete(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_undelete(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_entries(router, TargetTypeEnum.signature)
generic_tag_untag(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_source_add_remove(
    router, crud.signature, TargetTypeEnum.signature, schemas.Signature
)
generic_entities(router, TargetTypeEnum.signature)
generic_history(router, crud.signature, TargetTypeEnum.signature)
generic_search(router, crud.signature, TargetTypeEnum.signature, schemas.SignatureSearch, schemas.Signature)


@router.get(
    "/{id}/sigbodies",
    response_model=list[schemas.Sigbody],
    summary="Get a signature's signature bodies",
    dependencies=[
        Depends(deps.PermissionCheckId(TargetTypeEnum.signature, PermissionEnum.read))
    ],
)
def get_signature_sigbodies(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db)
) -> Any:
    return crud.sigbody.get_sigbodies_for_signature(db, id)


@router.get(
    "/{id}/links",
    response_model=Any,
    summary="Get a signature's links",
    dependencies=[
        Depends(deps.PermissionCheckId(TargetTypeEnum.signature, PermissionEnum.read))
    ],
)
def get_signature_links(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db)
) -> Any:
    results, count = crud.signature.retrieve_signature_links(db, id)
    return {"totalCount": count, "resultCount": len(results), "result": results}


# @router.get(
#    "/{id}/event_owners",
#    response_model=Any,
#    summary="Get a signature's links",
#    dependencies=[
#        Depends(deps.PermissionCheckId(TargetTypeEnum.signature, PermissionEnum.read))
#    ],
# )
# def get_user_stats(id: int, db: Session = Depends(deps.get_db)) -> Any:
#    results = crud.signature.get_event_owner_stats(db, id)
#    return results
#
# @router.get(
#    "/{id}/alert_stats",
#    response_model=Any,
#    summary="Get a signature's links",
#    dependencies=[
#        Depends(deps.PermissionCheckId(TargetTypeEnum.signature, PermissionEnum.read))
#    ],
# )
# def get_alert_stats(id: int, db: Session = Depends(deps.get_db)) -> Any:
#    results = crud.signature.get_alert_stats(db, id)
#    return results
#
# @router.get(
#    "/{id}/update_stats",
#    response_model=Any,
#    summary="Get a signature's links",
# )
#
# def update_stats(id: int, audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),db: Session = Depends(deps.get_db)) -> Any:
#    results = crud.signature.update_signature_stats(db_session=db, signature_id=id, audit_logger=audit_logger)
#    return results
#
# @router.get(
#    "/{id}/get_ranking",
#    response_model=Any,
#    summary="Get a signature's links",
# )
#
# def update_stats(id: int, audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),db: Session = Depends(deps.get_db)) -> Any:
#    results = crud.signature.sort_by_stat_rankings(db_session=db, signature_id=id, audit_logger=audit_logger)
#    return "good"
