from typing import Union

from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.crud.base import CRUDBase
from app.crud.crud_entry import entry
from app.crud.crud_link import link
from app.crud.crud_permission import permission
from app.crud.crud_source import source as crud_source
from app.crud.crud_tag import tag as crud_tag
from app.enums import EntryClassEnum, PermissionEnum, StatusEnum, TargetTypeEnum
from app.models.event import Event
from app.models.incident import Incident
from app.models.intel import Intel
from app.models.product import Product
from app.models.entry import Entry
from app.models.promotion import Promotion
from app.models.user import User
from app.schemas.alert import AlertUpdate
from app.schemas.entry import EntryCreate, EntryUpdate
from app.schemas.promotion import PromotionCreate, PromotionUpdate


class CRUDPromotion(CRUDBase[Promotion, PromotionCreate, PromotionUpdate]):
    def promote(
        self,
        db_session: Session,
        source: list[dict[str, Union[int, TargetTypeEnum]]],
        destination: TargetTypeEnum,
        destination_id: int | None = None,
        tags: list[str] | None = None,
        owner: User | None = None,
        sources: list[str] = None,
        permissions: dict[PermissionEnum, list] | None = None,
        audit_logger=None,
    ) -> Union[Event, Incident, Intel, Product]:
        """
        Promote one or more source objects (format: dict with keys "type" and
        "id") into a particular type of destination object
        Check permissions on the source object(s), as well as any destination
        object, before calling this method
        """
        if len(source) == 0:
            raise ValueError("Must promote from at least one source object")
        if any(["id" not in s or "type" not in s for s in source]):
            raise ValueError("All source objects must have a type and an id")
        # Find destination type
        self.target_type_mappings = [TargetTypeEnum.event, TargetTypeEnum.incident, TargetTypeEnum.intel, TargetTypeEnum.product, TargetTypeEnum.vuln_track]
        if destination not in self.target_type_mappings:
            raise ValueError("Support for %s not implemented" % destination)
        new_object_crud = self.target_crud_mapping[destination]
        # Create new destination object if not promoting to existing object
        new_attributes = {}
        if destination_id is None:
            # Pull info from first source object
            # Promoted object gets its attributes (subject, tlp, etc.) from the
            # first source object in the list
            first_object_type = TargetTypeEnum(source[0].get("type"))
            first_object_id = source[0].get("id")
            first_object_crud = self.target_crud_mapping[first_object_type]
            first_object = db_session.get(first_object_crud.model, first_object_id)
            # These are the only attributes copied. Make more?
            ATTRIBUTES_TO_COPY = ["subject", "tlp", "owner"]
            for a in ATTRIBUTES_TO_COPY:
                if not hasattr(new_object_crud.model, a):
                    continue
                if hasattr(first_object, a):
                    new_attributes[a] = getattr(first_object, a)
                # Special case for alert groups
                elif hasattr(first_object, "alertgroup") and hasattr(
                    first_object.alertgroup, a
                ):
                    new_attributes[a] = getattr(first_object.alertgroup, a)
            # Owner is always whoever promoted (if given)
            if hasattr(new_object_crud.model, "owner"):
                if owner is not None:
                    new_attributes["owner"] = owner.username
            # Make the new object and give it permissions
            new_object_class = new_object_crud.__orig_bases__[0].__args__[1]
            new_object_create = new_object_class(**new_attributes)
            if permissions is not None:
                promoted_object = new_object_crud.create_with_permissions(
                    db_session,
                    obj_in=new_object_create,
                    perm_in=permissions,
                    audit_logger=audit_logger,
                )
            else:
                # If no explicit permissions, copy source object permissions
                promoted_object = new_object_crud.create(
                    db_session, obj_in=new_object_create, audit_logger=audit_logger
                )
                permission.copy_object_permissions(
                    db_session,
                    first_object_type,
                    first_object_id,
                    destination,
                    promoted_object.id,
                )
        # If promoting to existing object, find it
        else:
            promoted_object = new_object_crud.get(db_session, destination_id)
            # Owner is always whoever promoted (if given)
            if hasattr(promoted_object, "owner"):
                if owner is not None:
                    new_attributes["owner"] = owner.username
                else:
                    new_attributes["owner"] = promoted_object.owner

            if promoted_object is None:
                raise ValueError(
                    "%s with id %s not found" % (destination.value, destination_id)
                )
        # Create the promotion object, as well as a link to all source objects
        for source_object in source:
            new_link = {
                "v0_type": destination,
                "v0_id": promoted_object.id,
                "v1_type": source_object["type"],
                "v1_id": source_object["id"],
                "weight": 1,
                "context": "Promoted from",
            }
            link.create(db_session, obj_in=new_link, audit_logger=audit_logger)
            promotion_create = {
                "p1_type": destination,
                "p1_id": promoted_object.id,
                "p0_type": source_object["type"],
                "p0_id": source_object["id"],
            }
            promotion.create(
                db_session, obj_in=promotion_create, audit_logger=audit_logger
            )
        # Add new tags and sources
        if tags:
            for t in tags:
                crud_tag.assign_by_name(
                    db_session,
                    t,
                    destination,
                    promoted_object.id,
                    create=True,
                    audit_logger=audit_logger,
                )
        if sources:
            for s in sources:
                crud_source.assign_by_name(
                    db_session,
                    s,
                    destination,
                    promoted_object.id,
                    create=True,
                    audit_logger=audit_logger,
                )
        # Add promotion entry to destination thing (unless it already has one)
        if destination_id is not None:
            entry_query = db_session.query(Entry).filter(
                (Entry.target_type == destination)
                & (Entry.target_id == destination_id)
                & (Entry.entry_class == EntryClassEnum.promotion)
            )
            promotion_entry = entry_query.first()
        if destination_id is None or promotion_entry is None:
            new_entry = EntryCreate(
                owner=new_attributes.get("owner"),
                target_type=destination,
                target_id=promoted_object.id,
                entry_class=EntryClassEnum.promotion,
                entry_data=jsonable_encoder({"promotion_sources": source}),
                audit_logger=audit_logger,
            )
            entry.create_in_object(
                db_session,
                obj_in=new_entry,
                source_type=destination,
                source_id=promoted_object.id,
            )
        else:
            old_sources = promotion_entry.entry_data["promotion_sources"]
            new_sources = old_sources + source
            new_data = {"promotion_sources": new_sources}
            entry.update(
                db_session=db_session,
                db_obj=promotion_entry,
                obj_in=EntryUpdate(entry_data=new_data),
                audit_logger=audit_logger,
            )
        # Change the status of the source elements to 'promoted'
        for s in source:
            _id = s.get("id")
            object_type = TargetTypeEnum(s.get("type"))
            object_crud = self.target_crud_mapping[object_type]
            _object = object_crud.get(db_session, _id)
            if object_type == TargetTypeEnum.alert:
                alert_update = AlertUpdate(
                    alertgroup_id=_object.alertgroup_id, status=StatusEnum.promoted
                )
                object_crud.update(
                    db_session=db_session,
                    db_obj=_object,
                    obj_in=alert_update,
                    audit_logger=audit_logger,
                )
            else:
                object_crud.update(
                    db_session=db_session,
                    db_obj=_object,
                    obj_in={"status": "promoted"},
                    audit_logger=audit_logger,
                )
        db_session.refresh(promoted_object)
        return promoted_object


promotion = CRUDPromotion(Promotion)
