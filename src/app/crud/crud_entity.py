import jinja2

from datetime import datetime
from typing import Union, get_args
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql.functions import coalesce
from sqlalchemy import and_, func, inspect

from app.core.config import settings
from app import crud
from app.enums import TargetTypeEnum, PermissionEnum
from app.crud.base import CRUDBase
from app.models import EntityClass, EntityType, User, Event, Incident, Dispatch, Product, Intel, Pivot, Enrichment, Entity, Link, Role, Promotion
from app.schemas.appearance import AppearanceCreate
from app.schemas.entity import EntityCreate, EntityUpdate
from app.schemas.entity_class import EntityClassCreate
from app.schemas.entity_type import EntityTypeCreate
from app.schemas.flair import FlairedEntity, FlairedTarget, FlairResults
from app.schemas.enrichment import EnrichmentCreate
from app.schemas.pivot import Pivot as PivotSchema


class CRUDEntity(CRUDBase[Entity, EntityCreate, EntityUpdate]):
    # Custom filtering for "value" field
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "value")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)
        # Ability to filter by entity class
        classes = filter_dict.pop("classes", None)
        not_classes = filter_dict.get("not", {}).pop("classes", None)
        if classes is not None:
            if isinstance(classes, list):
                query = query.filter(Entity.classes.any(EntityClass.name.in_(classes)))
            else:
                query = query.filter(Entity.classes.any(EntityClass.name == classes))
        if not_classes is not None:
            if isinstance(not_classes, list):
                query = query.filter(~Entity.classes.any(EntityClass.name.in_(not_classes)))
            else:
                query = query.filter(~Entity.classes.any(EntityClass.name == not_classes))

        return super().filter(query, filter_dict)

    # All entities are inherently queryable by anyone
    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read,
    ):
        return db_session.query(self.model)

    # Speed up entity counting since entities don't have permissions
    def get_count_from_query(self, query):
        return (
            query.group_by(None)
            .with_entities(func.count(inspect(self.model).primary_key[0]))
            .scalar()
        )

    def add_flair_results(
        self, db_session: Session, flair_results: FlairResults, audit_logger=None
    ):
        entity: FlairedEntity
        for entity in flair_results.entities:
            _entity = self.get_or_create(
                db_session=db_session,
                obj_in=EntityCreate(
                    value=entity.entity_value, type_name=entity.entity_type
                ),
                audit_logger=audit_logger
            )
            target: FlairedTarget
            for target in flair_results.targets:
                self.link_entity(
                    db_session,
                    _entity.id,
                    target.type,
                    target.id,
                    context="entity identified",
                    audit_logger=audit_logger,
                )

    def get_or_create(
        self, db_session: Session, obj_in: EntityCreate, audit_logger=None
    ) -> Entity:
        instance = (
            db_session.query(self.model)
            .filter(self.model.value == obj_in.value)
            .all()
        )
        if len(instance) > 0:
            instance = instance[0]  # this is to compensate for duplicate entry values for the time being.
            if audit_logger is not None:
                audit_logger.log("read", instance, log_thing=False)
            return instance
        else:
            type_id = None
            if obj_in.type_name is not None:
                # First check if the entity type exists
                type = (
                    db_session.query(EntityType)
                    .filter_by(name=obj_in.type_name)
                    .one_or_none()
                )
                if type is None:
                    # Need to create the entity type by the name
                    entity_type_create = jsonable_encoder(
                        EntityTypeCreate(name=obj_in.type_name)
                    )
                    entity_type_model = EntityType(**entity_type_create)
                    db_session.add(entity_type_model)
                    db_session.flush()
                    db_session.refresh(entity_type_model)
                    type_id = entity_type_model.id
                else:
                    type_id = type.id

            if obj_in.classes is not None:
                # Need to check
                new_classes = []
                for _class in obj_in.classes:
                    existing_class = (
                        db_session.query(EntityClass)
                        .filter_by(name=_class)
                        .one_or_none()
                    )
                    if existing_class is None:
                        entity_class_create = jsonable_encoder(
                            EntityClassCreate(name=_class)
                        )
                        entity_class_model = EntityClassCreate(**entity_class_create)
                        db_session.add(entity_class_model)
                        db_session.flush()
                        db_session.refresh(entity_class_model)
                        new_classes.append(entity_class_model)
                    else:
                        new_classes.append(existing_class)

            obj_in_data = jsonable_encoder(obj_in)
            del obj_in_data["type_name"]
            if "classes" in obj_in_data and obj_in_data["classes"] is None:
                del obj_in_data["classes"]
            else:
                obj_in_data["classes"] = new_classes
            obj_in_data["type_id"] = type_id
            db_obj = self.model(**obj_in_data)

            db_session.add(db_obj)
            db_session.flush()
            db_session.refresh(db_obj)
            if audit_logger is not None:
                audit_logger.log("create", db_obj)
            return db_obj

    def retrieve_element_entities(self, db_session: Session, source_id: int, source_type: TargetTypeEnum):
        element = self.target_crud_mapping[source_type].get(db_session, source_id)
        if not element:
            return [], 0
        link_query = db_session.query(Link).filter(
            and_(Link.v0_id == source_id, Link.v0_type == source_type, Link.v1_type == TargetTypeEnum.entity)
        )
        # We need an extra query in the other direction because of some migrated data
        # Can be removed if migrated links are fixed
        link_query_extra = db_session.query(Link).filter(
            and_(Link.v1_id == source_id, Link.v1_type == source_type, Link.v0_type == TargetTypeEnum.entity)
        )
        entity_ids = link_query.union(link_query_extra).all()
        # Also retrieve entities of things that were promoted to this item
        if hasattr(element, "promoted_from_sources") and element.promoted_from_sources:
            for promoted in element.promoted_from_sources:
                sub_link_query = db_session.query(Link).filter(
                    and_(Link.v0_id == promoted.p0_id,
                         Link.v0_type == promoted.p0_type,
                         Link.v1_type == TargetTypeEnum.entity)
                )
                sub_link_query_extra = db_session.query(Link).filter(
                    and_(Link.v1_id == promoted.p0_id,
                         Link.v1_type == promoted.p0_type,
                         Link.v0_type == TargetTypeEnum.entity)
                )
                entity_ids.extend(sub_link_query.union(sub_link_query_extra).all())

        if source_type != TargetTypeEnum.entity:
            entity_ids = [x.v0_id if x.v0_type == TargetTypeEnum.entity else x.v1_id for x in entity_ids]
        else:
            entity_ids = [x.v0_id if x.v1_id == source_id else x.v1_id for x in entity_ids]
        _entities = db_session.query(Entity).filter(Entity.id.in_(entity_ids)).all()

        return _entities, len(_entities)

    def retrieve_entity_links_for_flair_pane(self, db_session: Session, entity_id: int, skip: int = 0, limit: int = 10):
        element_dict = {
            TargetTypeEnum.alert: [],
            TargetTypeEnum.event: [],
            TargetTypeEnum.intel: [],
            TargetTypeEnum.dispatch: [],
            TargetTypeEnum.product: [],
            TargetTypeEnum.incident: [],
            TargetTypeEnum.signature: [],
            TargetTypeEnum.vuln_feed: [],
            TargetTypeEnum.vuln_track: []
        }
        # This window query has a subtle flaw - if something gets promoted,
        # the promotion source might not show up in this query if the promotion
        # target doesn't, even if it should. Waiting to fix this until entity
        # link directionality is fixed (it won't matter 99% of the time).
        links_sub_query = (
            db_session.query(Link.v0_id.label("id"),
                             Link.v0_type.label("type"),
                             Promotion.p1_type.label("p_type"),
                             Promotion.p1_id.label("p_id"))
            .join(Promotion,
                (Promotion.p0_id == Link.v0_id)
                & (Promotion.p0_type == Link.v0_type),
                isouter=True)
            .add_columns(func.row_number().over(
                partition_by=coalesce(Promotion.p1_type, Link.v0_type),
                order_by=coalesce(Promotion.created, Link.created).desc())
                .label("row_number"))
            .filter(
                (Link.v1_type == TargetTypeEnum.entity)
                & (Link.v1_id == entity_id)
                & (coalesce(Promotion.p1_type, Link.v0_type).in_(element_dict.keys()))
            )
            # We need an extra query in the other direction because of some migrated data
            # Can be removed if migrated links are fixed
            .union(
                db_session.query(Link.v1_id.label("id"),
                                 Link.v1_type.label("type"),
                                 Promotion.p1_type.label("p_type"),
                                 Promotion.p1_id.label("p_id"))
                .join(Promotion,
                    (Promotion.p0_id == Link.v1_id)
                    & (Promotion.p0_type == Link.v1_type),
                    isouter=True)
                .add_columns(func.row_number().over(
                    partition_by=coalesce(Promotion.p1_type, Link.v1_type),
                    order_by=coalesce(Promotion.created, Link.created).desc())
                    .label("row_number"))
                .filter(
                    (Link.v0_type == TargetTypeEnum.entity)
                    & (Link.v0_id == entity_id)
                    & (coalesce(Promotion.p1_type, Link.v1_type).in_(element_dict.keys()))
                )
            )
            .subquery()
        )
        entity_links = (
            db_session.query(links_sub_query)
            .filter(links_sub_query.c.row_number > skip)
            .filter(links_sub_query.c.row_number <= limit + skip)
            .all()
        )

        for entity_link in entity_links:
            if (entity_link.p_type is not None
                    and element_dict.get(entity_link.p_type) is not None):
                element_dict[entity_link.p_type].append(entity_link.p_id)
            if element_dict.get(entity_link.type) is not None:
                element_dict[entity_link.type].append(entity_link.id)

        appearances = {}
        for element_type, element_ids in element_dict.items():
            # We want to get the alerts (with the alertgroup subject and id), events, intels, dispatches, products, incidents, or signatures.
            appearances[f"{element_type.value}_appearances"] = []
            # Get model as first generic parameter of crud type (mapped from target type)
            model = get_args(self.target_crud_mapping[element_type].__orig_bases__[0])[0]
            appearances_get = (
                db_session.query(model)
                .filter(model.id.in_(element_ids))
                .order_by(model.created.desc())
                .limit(limit)
                .all()
            )
            for appearance in appearances_get:
                appearance_dict = {
                    "id": appearance.id,
                    "type": element_type,
                    "last_updated": appearance.modified,
                    "subject": getattr(appearance, "subject", None),
                    "status": appearance.status if hasattr(appearance, "status") else "",
                }

                if element_type == TargetTypeEnum.alert:
                    appearance_dict["alertgroup_id"] = appearance.alertgroup_id
                    appearance_dict["subject"] = appearance.alertgroup_subject
                    appearance_dict["promoted_ids"] = [x.p1_id for x in appearance.promoted_to_targets]
                if element_type == TargetTypeEnum.signature:
                    appearance_dict["subject"] = appearance.name

                appearances[f"{element_type.value}_appearances"].append(appearance_dict)

        return appearances

    def retrieve_entity_pivots(self, db_session: Session, entity_id: int):
        all_pivots = []
        entity = self.get(db_session, entity_id)
        if entity:
            entity_type_pivots = db_session.query(Pivot).filter(Pivot.entity_types.any(id=entity.type_id)).all()
            for entity_type_pivot in entity_type_pivots:
                if len(entity_type_pivot.entity_classes) == 0:
                    all_pivots.append(entity_type_pivot)
                elif len(set([x.id for x in entity.classes]).intersection(set([x.id for x in entity_type_pivot.entity_classes]))) > 0:
                    all_pivots.append(entity_type_pivot)
                else:
                    pass

            environment = jinja2.Environment(autoescape=True)
            pivot: PivotSchema
            for pivot in all_pivots:
                template = environment.from_string(pivot.template)
                pivot_value = template.render(entity=entity.value)
                pivot.pivot_value = pivot_value

        return all_pivots, len(all_pivots)

    def link_entity(
        self,
        db_session: Session,
        entity_id: int,
        target_type: TargetTypeEnum,
        target_id: int,
        context: str = "linked to",
        audit_logger=None,
        skip_duplicate: bool = True
    ):
        # Make sure entity exists (use cache if we can)
        entity = db_session.get(Entity, entity_id)
        if entity is None:
            return None

        # Link entity to given object
        new_link = {
            "v0_type": target_type,
            "v0_id": target_id,
            "v1_type": TargetTypeEnum.entity,
            "v1_id": entity_id,
            "weight": 1,
            "context": context
        }

        # If there's already an identical link, don't link
        link_check = db_session.query(Link).filter_by(**new_link).first()
        if not link_check or not skip_duplicate:
            crud.link.create(db_session, obj_in=new_link, audit_logger=audit_logger)
            # Add to appearances table
            new_appearance = AppearanceCreate(
                when_date=datetime.utcnow(),
                target_type=target_type,
                target_id=target_id,
                value_type=TargetTypeEnum.entity.value,
                value_id=entity_id,
                value_str=entity.value,
            )
            crud.appearance.create(db_session, obj_in=new_appearance, audit_logger=audit_logger)

        return entity

    def add_enrichment(
        self, 
        db_session: Session, 
        entity_id: int, 
        enrichment: EnrichmentCreate,
        audit_logger=None
    ):
        entity = self.get(db_session=db_session, _id=entity_id)
        if entity is None:
            return None

        current_enrichments_with_same_name = entity.available_enrichments.get(enrichment.title)
        enrichment = Enrichment(**enrichment.model_dump())
        if current_enrichments_with_same_name is None:
            entity.enrichments.append(enrichment)
        elif len(current_enrichments_with_same_name) > 0 and len(current_enrichments_with_same_name) < settings.MAX_ENRICHMENT_BY_NAME:
            entity.enrichments.append(enrichment)
        else:
            # We need to remove the earliest enrichment with this same title
            crud.enrichment.remove(db_session=db_session, _id=current_enrichments_with_same_name[-1].id)
            entity.enrichments.append(enrichment)

        db_session.refresh(entity)
        db_session.flush()
        if audit_logger is not None:
            audit_logger.log("create", enrichment)
        return entity

    def add_entity_classes(
        self,
        db_session: Session,
        entity_id: int,
        entity_classes: list[Union[int, str]],
        audit_logger=None
    ) -> Entity:
        """
        Adds entity classes to an entity
        """
        entity = self.get(db_session=db_session, _id=entity_id)
        if entity is None:
            return entity

        for _id in entity_classes:
            if isinstance(_id, int):
                entity_class = crud.entity_class.get(db_session=db_session, _id=_id)
                if entity_class is not None:
                    entity.classes.append(entity_class)
            elif isinstance(_id, str):
                entity_class = db_session.query(EntityClass).filter(EntityClass.name == _id).one_or_none()
                if entity_class is not None:
                    entity.classes.append(entity_class)
                else:
                    # Create a new entity class with no icon and no description
                    new_entity_class = EntityClassCreate(name=_id, display_name=_id)
                    entity_class = crud.entity_class.create(db_session=db_session, obj_in=new_entity_class)
                    entity.classes.append(entity_class)

        db_session.add(entity)
        db_session.flush()
        db_session.refresh(entity)

        if audit_logger is not None:
            audit_logger.log("update", {"classes": entity.classes},
                             thing_type=TargetTypeEnum.entity, thing_pk=entity_id)
        return entity

    def remove_entity_classes(
        self,
        db_session: Session,
        entity_id: int,
        entity_classes: list[int],
        audit_logger=None
    ):
        """
        Removes entity classes to an entity
        """
        entity = self.get(db_session=db_session, _id=entity_id)
        if entity is None:
            return None

        for _id in entity_classes:
            entity_class = crud.entity_class.get(db_session=db_session, _id=_id)
            if entity_class is not None:
                entity.classes.remove(entity_class)

        db_session.add(entity)
        db_session.flush()
        db_session.refresh(entity)

        if audit_logger is not None:
            audit_logger.log("update", {"classes": entity.classes},
                             thing_type=TargetTypeEnum.entity, thing_pk=entity_id)
        return entity

    def link_entity_by_value(
        self,
        db_session: Session,
        entity_value: str,
        target_type: TargetTypeEnum,
        target_id: int,
        create: bool = True,
        context: str = "linked to",
        entity_type: str | None = None,
        entity_class: list[str] = [],
        audit_logger=None,
        skip_duplicate: bool = True
    ):
        """
        Links an object to an entity by that entity's text value. The text
        must be an exact match. By default, the entity is created if it
        does not exist.
        """
        # Delegate to get_or_create if create flag
        if create:
            new_entity = EntityCreate(value=entity_value, classes=entity_class, type_name=entity_type)
            entity = self.get_or_create(db_session, obj_in=new_entity, audit_logger=audit_logger)
        else:
            query = db_session.query(self.model).filter(
                self.model.value == entity_value
            )
            if entity_type is not None:
                query = query.filter(self.model.type_name == entity_type)
            entity = query.first()

            if entity_class is not None and entity is not None:
                if set(entity_class) != set([a.name for a in entity.classes]):
                    entity = None

            if entity is None:
                return None

        return self.link_entity(
            db_session, entity.id, target_type, target_id, context,
            audit_logger, skip_duplicate
        )


entity = CRUDEntity(Entity)
