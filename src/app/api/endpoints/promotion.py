from typing import Union, Annotated
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.enums import PermissionEnum, TargetTypeEnum

router = APIRouter()

description = f"""
Promote an object to another object, either an existing object or a new one. A
promotion entry will be created in the new object if one does not already exist.
The default promotion pathways are as follows:
 - Alert -> Event -> Incident
 - Dispatch -> Intel -> Product
 - Vuln feed -> Vuln track

### Fields
 - `source`

   - Required: `True`

   - Type: `array[object]`

   - Description: A list of sources that you want to promote, in the format
        {{"type": "alert", "id": 1}}, for example; all sources will be promoted to the
        same destination

 - `destination`

   - Required: `True`

   - Type: `string`

     - Choices: `event`, `incident`, `intel`, `product`, `vuln_track`

   - Description: The type of object to promote the source(s) to

 - `destination_id`

   - Required: `False`

   - Type: `integer` or `null`

   - Description: The id of an existing object to promote the source(s) to
        (null means make a new destination object)

 - `tags`

   - Required: `False`

   - Type: `array[string]`

   - Description: The tags to add to the destination object, if any

 - `sources`

   - Required: `False`

   - Type: `array[string]`

   - Description: The sources to add to the destination object, if any

 - `permissions`

   - Required: `False`

   - Type: object

   - Description: Grant permissions on the new destination object, if one was created.
        Provide a dictionary with the permission type as the key and a list of role
        ids or role names
"""


# Response model is union of every possible target type
# I'm not sure there's a better way to do this
# Right now this misbehaves when promoting to something weird (like an entity)
# Ordering in the response model list usually causes the correct behavior
@router.post(
    "/",
    response_model=Union[
        schemas.Event,
        schemas.Incident,
        schemas.Intel,
        schemas.Product,
        schemas.VulnTrack
    ],
    summary="Promote an object",
    description=description
)
def promote(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_roles: list[models.Role] = Depends(deps.get_current_roles),
    audit_logger: deps.AuditLogger = Depends(deps.get_audit_logger),
    source: Annotated[list[dict], Body(..., examples=[[{"type": "alert", "id": 1}, {"type": "alert", "id": 2}]])],
    destination: Annotated[TargetTypeEnum, Body(..., examples=["event"])],
    destination_id: Annotated[int | None, Body(..., examples=[None])] = None,
    tags: Annotated[list[str] | None, Body(...)] = None,
    sources: Annotated[list[str] | None, Body()] = None,
    permissions: Annotated[dict[PermissionEnum, list[str | int]] | None, Body(...,
        examples=[{a.value: [1, "rolename"] for a in list(PermissionEnum)
        if a != PermissionEnum.admin}]
    )] = None
):
    """
    Promote one or more source objects into a destination object
    """
    # Check permissions on source objects
    try:
        for s in source:
            target_type = s["type"]
            target_id = s["id"]
            if not deps.PermissionCheckId(target_type, PermissionEnum.read)(target_id, db, current_user, current_roles):
                raise ValueError(f"{target_type} with id {target_id} does not exist or you do not have permission to access it")
    except (IndexError, ValueError) as e:
        raise HTTPException(422, f"Error processing promotion: {e}")
    # User needs modify permissions on the destination if it already exists
    if destination_id is not None:
        if not deps.PermissionCheckId(destination, PermissionEnum.modify)(destination_id, db, current_user, current_roles):
            raise HTTPException(422, f"{destination.value} with id {destination_id} does not exist or you do not have permission to modify it")
    # Do the promotion
    try:
        return crud.promotion.promote(db, source, destination, destination_id, tags, current_user, sources, permissions, audit_logger)
    except ValueError as e:
        raise HTTPException(422, f"Error processing promotion: {e}")
