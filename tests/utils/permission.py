import random

from typing import Any, Union
from sqlalchemy.orm import Session

from app import crud
from app.enums import PermissionEnum, TargetTypeEnum
from app.models.alert import Alert
from app.models.alertgroup import AlertGroup
from app.models.checklist import Checklist
from app.models.dispatch import Dispatch
from app.models.entity import Entity
from app.models.entry import Entry
from app.models.event import Event
from app.models.file import File
from app.models.guide import Guide
from app.models.incident import Incident
from app.models.intel import Intel
from app.models.product import Product
from app.models.sigbody import Sigbody
from app.models.signature import Signature
from app.models.source import Source
from app.models.stat import Stat
from app.models.tag import Tag
from app.schemas.permission import PermissionCreate
from app.schemas.role import Role
from app.schemas.vuln_feed import VulnFeed
from app.schemas.vuln_track import VulnTrack


def create_random_permission(db: Session, role: Union[Role, list[Role]], target: Any):
    if isinstance(target, Alert):
        target_type = TargetTypeEnum.alert
    elif isinstance(target, AlertGroup):
        target_type = TargetTypeEnum.alertgroup
    elif isinstance(target, Checklist):
        target_type = TargetTypeEnum.checklist
    elif isinstance(target, Dispatch):
        target_type = TargetTypeEnum.dispatch
    elif isinstance(target, Entity):
        target_type = TargetTypeEnum.entity
    elif isinstance(target, Entry):
        target_type = TargetTypeEnum.entry
    elif isinstance(target, Event):
        target_type = TargetTypeEnum.event
    elif isinstance(target, File):
        target_type = TargetTypeEnum.file
    elif isinstance(target, Guide):
        target_type = TargetTypeEnum.guide
    elif isinstance(target, Incident):
        target_type = TargetTypeEnum.incident
    elif isinstance(target, Intel):
        target_type = TargetTypeEnum.intel
    elif isinstance(target, Product):
        target_type = TargetTypeEnum.product
    elif isinstance(target, Sigbody):
        target_type = TargetTypeEnum.sigbody
    elif isinstance(target, Signature):
        target_type = TargetTypeEnum.signature
    elif isinstance(target, Source):
        target_type = TargetTypeEnum.source
    elif isinstance(target, Stat):
        target_type = TargetTypeEnum.stat
    elif isinstance(target, Tag):
        target_type = TargetTypeEnum.tag
    elif isinstance(target, VulnFeed):
        target_type = TargetTypeEnum.vuln_feed
    elif isinstance(target, VulnTrack):
        target_type = TargetTypeEnum.vuln_track
    # elif what is admin????
    else:
        target_type = random.choice(list(TargetTypeEnum))
    target_id = target.id

    # make sure admins can access the same data
    # as far as I can tell admins must have read rights to the data
    admin_role = crud.role.get_role_by_name(db, name="admin")
    permission_create = PermissionCreate(
        role_id=admin_role.id,
        target_type=target_type,
        target_id=target_id,
        permission=PermissionEnum.read,
    )
    crud.permission.create(db, obj_in=permission_create)

    if not isinstance(role, list):
        role = [role]

    # must have at least read permissions on the data
    permission_create = PermissionCreate(
        role_id=role[0].id,
        target_type=target_type,
        target_id=target_id,
        permission=PermissionEnum.read,
    )

    permission = crud.permission.create(db, obj_in=permission_create)

    for r in role[1:]:
        permission_create.role_id = r.id
        crud.permission.grant_permission(db, permission_create)

    return permission
