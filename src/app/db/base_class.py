import enum

from typing import Any
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy.orm import as_declarative, declared_attr

from app.enums import TargetTypeEnum


@as_declarative()
class Base:
    """ """

    id: Any
    __name__: str

    # Default table name is name of the class
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    def as_dict(self, exclude_keys=["entity_type", "tag_type", "entity_types", "entity_classes", "permissions"], pretty_keys: bool = False, enum_value: bool = False):
        """
        Serializes this model to a dictionary as accurately as possible
        Contains logic to prevent infinite recursion for circular references
        """
        no_serialize = set()

        def process_item(item):
            result = None
            # Lists
            if isinstance(item, list):
                result = []
                for lval in item:
                    list_item = process_item(lval)
                    if list_item or not lval:
                        # Skip adding item if it's falsy now, but wasn't
                        # before removing recursive references and such
                        result.append(list_item)
            # Dictionaries
            elif isinstance(item, dict):
                result = {}
                for key in item:
                    dict_item = process_item(item[key])
                    if dict_item or not item[key]:
                        # Skip adding item if it's falsy now, but wasn't
                        # before removing recursive references and such
                        if pretty_keys:
                            key = key.replace("_", " ")
                        result[key] = dict_item
            # DB models - only ever serialize a particular model once
            elif isinstance(item, Base):
                if item in no_serialize:
                    result = None
                else:
                    result = {}
                    no_serialize.add(item)
                    for attr in inspect(item).attrs:
                        if attr.key in exclude_keys:
                            continue
                        # Specifically exclude items starting with parent_
                        # on entries, as those are sort of hackish
                        if (type(item).__name__ == "Entry"
                                and attr.key.startswith("parent_")):
                            continue
                        processed_attr = process_item(attr.value)
                        if processed_attr or not attr.value:
                            # Skip adding item if it's falsy now, but wasn't
                            # before removing recursive references and such
                            key = attr.key
                            if pretty_keys:
                                key = attr.key.replace("_", " ")
                            result[key] = processed_attr
            elif isinstance(item, enum.Enum) and enum_value:
                result = item.value
            elif isinstance(item, datetime):
                result = item.isoformat()
            # Everything else
            else:
                result = item
            return result

        # Return the result of process_item on this object
        return process_item(self)

    target_type_mapping = {
        "alerts": TargetTypeEnum.alert,
        "alertgroups": TargetTypeEnum.alertgroup,
        "checklists": TargetTypeEnum.checklist,
        "dispatches": TargetTypeEnum.dispatch,
        "entities": TargetTypeEnum.entity,
        "entries": TargetTypeEnum.entry,
        "events": TargetTypeEnum.event,
        "files": TargetTypeEnum.file,
        "guides": TargetTypeEnum.guide,
        "incidents": TargetTypeEnum.incident,
        "intels": TargetTypeEnum.intel,
        "products": TargetTypeEnum.product,
        "sigbodies": TargetTypeEnum.sigbody,
        "signatures": TargetTypeEnum.signature,
        "entity_classes": TargetTypeEnum.entity_class,
        "entity_types": TargetTypeEnum.entity_type,
        "sources": TargetTypeEnum.source,
        "stats": TargetTypeEnum.stat,
        "tags": TargetTypeEnum.tag,
        "threat_model_items": TargetTypeEnum.threat_model_item,
        "feeds": TargetTypeEnum.feed,
        "pivots": TargetTypeEnum.pivot,
        "vuln_feeds": TargetTypeEnum.vuln_feed,
        "vuln_tracks": TargetTypeEnum.vuln_track
    }

    @classmethod
    def target_type_enum(cls) -> TargetTypeEnum:
        if cls.__tablename__ in cls.target_type_mapping:
            return cls.target_type_mapping[cls.__tablename__]
        else:
            # Use table name directly if not mapped
            return TargetTypeEnum(cls.__tablename__)

    @classmethod
    def get_model_by_target_type(cls, target_type: TargetTypeEnum):
        """
        Gets a model from a target type enum
        """
        table_name = list(cls.target_type_mapping.keys())[list(cls.target_type_mapping.values()).index(target_type)]
        if table_name is not None:
            registry_instance = getattr(cls, "registry")
            for mapper_ in registry_instance.mappers:
                if (mapper_.class_.__tablename__ == table_name):
                    return mapper_.class_