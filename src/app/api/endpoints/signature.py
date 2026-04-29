import json
import os

from packaging.version import Version
from typing import Any, Annotated
from fastapi import APIRouter, Depends, Path, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app import crud, schemas, models
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum, ThreatModelName
from app.utils import create_schema_details, get_search_filters
from app.core.config import settings

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
    generic_export,
    generic_upvote_and_downvote,
    generic_user_links,
    generic_get_threat_model_items
)

router = APIRouter()

# Create get, post, put, delete, entries, tag, and source endpoints
generic_get(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_post(router, crud.signature, TargetTypeEnum.signature, schemas.Signature, schemas.SignatureCreate)
generic_put(router, crud.signature, TargetTypeEnum.signature, schemas.Signature, schemas.SignatureUpdate)
generic_delete(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_search(router, crud.signature, TargetTypeEnum.signature, schemas.SignatureSearch, schemas.Signature)
generic_undelete(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_entries(router, TargetTypeEnum.signature)
generic_tag_untag(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_source_add_remove(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_entities(router, TargetTypeEnum.signature)
generic_history(router, crud.signature, TargetTypeEnum.signature)
generic_export(router, crud.signature, TargetTypeEnum.signature)
generic_upvote_and_downvote(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_user_links(router, crud.signature, TargetTypeEnum.signature, schemas.Signature)
generic_get_threat_model_items(router, crud.signature, TargetTypeEnum.signature)


@router.get(
    "/{id}/links",
    response_model=Any,
    summary="Get a signature's links",
    dependencies=[Depends(deps.PermissionCheckId(TargetTypeEnum.signature, PermissionEnum.read))],
)
def get_signature_links(
    id: Annotated[int, Path(...)],
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get all objects linked to this signature
    """
    results, count = crud.signature.retrieve_signature_links(db, id)
    return {"totalCount": count, "resultCount": len(results), "result": results}


@router.get(
    "/attack_navigator",
    summary="Generate a MITRE ATT&CK Navigator JSON file",
)
def navigator(
    search_schema: schemas.SignatureSearch = Depends(),
    db: Session = Depends(deps.get_db),
    _: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
):
    """
    ### Generate a MITER ATT&CK Navigator JSON file, optionally filtering on one or more available fields
    Only signatures that have an associated MITRE ATT&CK Threat Model Item and that match all filters will
    be returned. The filters can be modified using the syntax below.
    | | |
    | --- | --- |
    | `!` | return the opposite result |
    | `(n, n1)` | select values within the given range |
    | `!(n, n1)` | select values **NOT** within the given range |
    | `[n, n1, n2, ...]` | select multiple values within a list |
    | `![n, n1, n2, ...]` | select **NOT** multiple values within a list |
    | `\\` | use a backslash to escape a special character at the beginning of your search string; you must escape a starting parenthesis `(`, bracket `[`, or exclamation point `!` or it will be interpreted as above |

    ### Examples:
    | | |
    | --- | --- |
    | `id=1` | return all items with ids that match the value |
    | `id=!1` | return all items with ids that don't match the value |
    | `modified=(2024-01-01, 2024-01-02)` | return all items last modified between the dates |
    | `modified=!(2024-01-01, 2024-01-02)` | return all items that were not last modified between the dates |
    | `owner=[alice, bob]` | return all items that have any of the listed owners |
    | `owner=![charlie, dave]` | return all items that don't have any of the listed owners |
    | `name=\\!test` | return all items with names that match including the `!`, but not including the `\\`|
    | `name=\\(test)` | return all items with names that match including the `(` and `)`, but not including the `\\` |

    ### Notes:
    - Non-numeric/non-date fields can't use the range filters, for example `subject` or `description`. If range filters are provided the system will treat them as a list filter instead.
    - If none of the range or list filters work it will attempt to do a normal search
    - Datetimes are parsed using the [dateutil module](https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse)
    - Some fields (e.g. event subjects and entity values) default to "contains" string searches, where any item containing the searched string will match (so searching for `example.com` would match both `example.com` and `foo.example.com`). Searching these fields with list searches (with square brackets) disables this feature for all list items, but "range" searches (with parentheses) search normally. For example, searching `[example.com]` wouldn't match `foo.example.com` but searching `(example.com)` would match.
    """

    try:
        filter_dict = get_search_filters(search_schema)
        filter_dict["threat_model_name"] = ThreatModelName.attack
        _result, _count = crud.signature.query_with_filters(db, current_roles, filter_dict)

        navigator = {
            "name": "SCOT Signatures",
            "versions": {
                "attack": "",
                "layer": "4.5"
            },
            "domain": "enterprise-attack",
            "techniques": []
        }

        if _count > 0:
            version = Version("0")
            scot_url_base = settings.API_EXTERNAL_BASE.replace(settings.API_V1_STR, "")
            for signature in _result:
                for threat_model_item in signature.associated_threat_model_items:
                    if threat_model_item.threat_model_name == ThreatModelName.attack:
                        if Version(threat_model_item.data["version"]) > version:
                            version = Version(threat_model_item.data["version"])

                        for tactic in threat_model_item.data["tactics"]:
                            navigator["techniques"].append({
                                "techniqueID": threat_model_item.threat_model_id,
                                "tactic": tactic,
                                "color": "#31a354",
                                "links": [{
                                    "label": f"SCOT Signature {signature.id}",
                                    "url": f"{scot_url_base}/#/signatures/{signature.id}"
                                }]
                            })
            
            navigator["versions"]["attack"] = str(version)

        with open(f"scot_signatures.json", "w") as f:
            json.dump(navigator, f)
        
        return FileResponse(
            "scot_signatures.json",
            filename="scot_signatures.json",
            background=BackgroundTask(os.remove, "scot_signatures.json")
        )
    except ValueError as e:
        raise HTTPException(422, str(e))


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
