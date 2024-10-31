from typing import Union
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.crud.base import CRUDBase
from app.models.pivot import Pivot
from app.models.entity_class import EntityClass
from app.models.entity_type import EntityType
from app.schemas.pivot import PivotCreate, PivotUpdate


class CRUDPivot(CRUDBase[Pivot, PivotCreate, PivotUpdate]):
    def add_entity_classes(self, db_session: Session = None, db_obj: Pivot = None, entity_classes: list[Union[int, str]] = None, audit_logger=None):
        entity_classes_to_add = []
        for entity_class_identifier in entity_classes:
            _entity_class = None
            if isinstance(entity_class_identifier, str):
                _entity_class = db_session.query(EntityClass).filter(EntityClass.name == entity_class_identifier).one_or_none()
                entity_classes_to_add.append(_entity_class)

            elif isinstance(entity_class_identifier, int):
                _entity_class = db_session.query(EntityClass).filter(EntityClass.id == entity_class_identifier).one_or_none()
                entity_classes_to_add.append(_entity_class)
        if None in entity_classes_to_add:
            raise Exception("One of more entity classes specified do not exist, please try again with valid entity class id's or names")

        db_obj.entity_classes = entity_classes_to_add
        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)
        if audit_logger is not None:
            primary_key = inspect(db_obj).identity[0]
            thing_type = db_obj.target_type_enum()
            audit_logger.log(
                "Link Pivot to Entity Class", entity_classes, thing_type=thing_type, thing_pk=primary_key
            )
        return db_obj

    def add_entity_types(self, db_session: Session = None, db_obj: Pivot = None, entity_types: list[Union[int, str]] = None, audit_logger=None):
        entity_types_to_add = []
        for entity_type_identifier in entity_types:
            _entity_type = None
            if isinstance(entity_type_identifier, str):
                _entity_type = db_session.query(EntityType).filter(EntityType.name == entity_type_identifier).one_or_none()
                entity_types_to_add.append(_entity_type)

            elif isinstance(entity_type_identifier, int):
                _entity_type = db_session.query(EntityType).filter(EntityType.id == entity_type_identifier).one_or_none()
                entity_types_to_add.append(_entity_type)

        if None in entity_types_to_add:
            raise Exception("One of more entity types specified do not exist, please try again with valid entity type id's or names")

        db_obj.entity_types = entity_types_to_add
        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)
        if audit_logger is not None:
            primary_key = inspect(db_obj).identity[0]
            thing_type = db_obj.target_type_enum()
            audit_logger.log(
                "Link Pivot to Entity Types", entity_types, thing_type=thing_type, thing_pk=primary_key
            )
        return db_obj


pivot = CRUDPivot(Pivot)
