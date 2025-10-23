from typing import Any, Generic, Type, TypeVar, Union

from dateutil.parser import parse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import distinct, func, inspect, or_, and_
from sqlalchemy.orm import Session, aliased, Query

from app.core.config import settings
from app.db.base_class import Base
from app.enums import PermissionEnum, TargetTypeEnum
from app.models import Permission, Role, User, Link, Tag, Source, Audit, Promotion, Popularity
from app.utils import escape_sql_like

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    global_subscribers = {}
    target_crud_mapping = {}

    def __init__(self, model: Type[ModelType], tt=None):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**

        * `model`: A SQLAlchemy model class
        * `target_type`: A target type for setting permissions
        """
        self.model = model
        if self.model.target_type_enum() != TargetTypeEnum.none:
            self.target_crud_mapping[self.model.target_type_enum()] = self

    def get(self, db_session: Session, _id: Any, audit_logger=None) -> ModelType | None:
        """
        Get a single object from DB
        :param db_session:
        :param _id:
        :return:
        """
        CRUDBase.publish("get", _id)
        obj = db_session.query(self.model).filter(self.model.id == _id).first()

        if audit_logger is not None:
            audit_logger.log("read", obj, thing_pk=_id, log_thing=False)
        return obj

    def get_multi(
        self,
        db_session: Session,
        *,
        skip: int = 0,
        limit: int | None = None,
        audit_logger=None,
    ) -> list[ModelType]:
        """
        Get many objects from DB
        :param db_session:
        :param skip:
        :param limit:
        :return:
        """
        self.publish("get_multi")
        objs = db_session.query(self.model).offset(skip).limit(limit).all()
        if audit_logger is not None:
            for obj in objs:
                audit_logger.log("read", obj, log_thing=False)
        return objs

    def create(
        self,
        db_session: Session,
        *,
        obj_in: Union[CreateSchemaType, dict],
        audit_logger=None
    ) -> ModelType:
        if isinstance(obj_in, BaseModel):
            obj_in_data = obj_in.model_dump()
        else:
            obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)
        CRUDBase.publish("create", db_obj)
        if audit_logger is not None:
            audit_logger.log("create", db_obj)
        return db_obj

    @staticmethod
    def update(
        db_session: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, dict[str, Any]],
        audit_logger=None,
    ) -> ModelType:
        obj_data_fields = [a.key for a in inspect(db_obj).attrs]
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data_fields:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db_session.add(db_obj)
        db_session.flush()
        db_session.refresh(db_obj)
        CRUDBase.publish("create", update_data)
        if audit_logger is not None:
            primary_key = inspect(db_obj).identity[0]
            thing_type = db_obj.target_type_enum()
            if thing_type == TargetTypeEnum.none:
                thing_type = type(db_obj).__name__.lower()
            audit_logger.log(
                "update", update_data, thing_type=thing_type, thing_pk=primary_key
            )
        return db_obj

    def remove(self, db_session: Session, *, _id: int, audit_logger=None) -> ModelType:
        obj = db_session.get(self.model, _id)
        if obj is not None:
            db_session.delete(obj)
            db_session.flush()
            if audit_logger is not None:
                audit_logger.log("delete", obj)
        return obj

    def get_or_create(
        self,
        db_session: Session,
        obj_in: Union[CreateSchemaType, dict[str, Any]],
        audit_logger=None,
    ) -> ModelType:
        if isinstance(obj_in, BaseModel):
            obj_in_data = obj_in.model_dump(exclude_unset=True)
        else:
            obj_in_data = jsonable_encoder(obj_in)

        instance = (
            db_session.query(self.model)
            .filter_by(**obj_in_data)
            .one_or_none()
        )
        if instance:
            if audit_logger is not None:
                audit_logger.log("read", instance, log_thing=False)
            return instance
        else:
            db_obj = self.model(**obj_in_data)
            db_session.add(db_obj)
            db_session.flush()
            db_session.refresh(db_obj)
            if audit_logger is not None:
                audit_logger.log("create", db_obj)
            return db_obj

    def query_with_filters(
        self,
        db_session: Session,
        roles: list[Role] = None,
        filter_dict: dict = None,
        sort_string: str = None,
        skip: int = 0,
        limit: int | None = None,
        audit_logger=None,
    ):
        # Just normal query if a role is an admin role, or if no roles were given
        from app.crud import permission
        # Performs a query while filtering, sorting, and paginating appropriately
        # Query with permissions if set of roles given
        if roles is None or permission.roles_have_admin(db_session, roles):
            query = db_session.query(self.model)
        else:
            query = self.query_objects_with_roles(db_session, roles)
        # Filter if filter dict given
        if filter_dict is not None:
            query = self.filter(query, filter_dict)
        # Get total count before LIMIT or SKIP
        count = self.get_count_from_query(query)
        # Sort if sort string provided
        if sort_string is not None:
            query = self.sort(query, sort_string)
        # Negative limit same as limit = None
        if limit and limit < 0:
            limit = None
        if skip and skip > 0:
            query = query.offset(skip)

        result = query.limit(limit).all()
        if audit_logger is not None:
            for item in result:
                audit_logger.log("read", item, log_thing=False)
        return result, count

    def get_count_from_query(self, query):
        """
        Returns a scalar count of the total number of objects in the query
        Can be overridden in subclasses for efficiency
        """
        # This is more efficient than query.count() most of the time
        return (
            query.group_by(None)
            .with_entities(func.count(distinct(inspect(self.model).primary_key[0])))
            .scalar()
        )

    # some very common filters that a lot of crud filters need
    def _str_filter(self, query: Query, filter_dict: dict, column: str, escape: bool = True):
        # check if model has column
        if hasattr(self.model, column):
            model = getattr(self.model, column)
            column_obj = filter_dict.pop(column, None)
            if column_obj is not None:
                # does this even make sense? raise exception or just treat it like range?
                if isinstance(column_obj, tuple):
                    condition = []
                    for item in column_obj:
                        if escape:
                            condition.append(model.like(f"%{escape_sql_like(item)}%"))
                        else:
                            condition.append(model.like(f"%{item}%"))
                    query = query.filter(or_(*condition))
                # If it's a list, disable string contains querying
                elif isinstance(column_obj, list):
                    condition = []
                    for item in column_obj:
                        condition.append(model == item)
                    query = query.filter(or_(*condition))
                else:
                    if escape:
                        t = escape_sql_like(column_obj)
                        query = query.filter(
                            model.like(f"%{t}%")
                        )
                    else:
                        query = query.filter(
                            model.like(f"%{column_obj}%")
                        )

            # check for not conditions
            column_obj = filter_dict.get("not", {}).pop(column, None)
            if column_obj is not None:
                # does this even make sense? raise exception or just treat it like range?
                if isinstance(column_obj, tuple) or isinstance(column_obj, list):
                    condition = []
                    for item in column_obj:
                        if escape:
                            condition.append(model.not_like(f"%{escape_sql_like(item)}%"))
                        else:
                            condition.append(model.not_like(f"%{item}%"))
                    query = query.filter(and_(*condition))
                else:
                    if escape:
                        query = query.filter(
                            model.not_like(f"%{escape_sql_like(column_obj)}%")
                        )
                    else:
                        query = query.filter(
                            model.not_like(f"%{column_obj}%")
                        )

        return query

    def _promoted_to_or_from_filter(self, query: Query, filter_dict: dict, direction: str):
        # helper function to split the filter into type and id parts
        # "promoted_*" field takes input in the form <type>:<id>, e.g. event:1
        def _promotion_split(fields: str):
            field_parts = fields.split(":", 1)
            if len(field_parts) == 2:
                return TargetTypeEnum(field_parts[0]).value, int(field_parts[1])
            else:
                return None, None

        # used to determine the main queries for either promoted to or from directions
        if direction == "to":
            filter_target = "promoted_to"
        elif direction == "from":
            filter_target = "promoted_from"
        promoted = filter_dict.pop(filter_target, None)
        not_promoted = filter_dict.get("not", {}).pop(filter_target, None)
        if promoted is not None or not_promoted is not None:
            if direction == "to":
                model_target = self.model.promoted_to_targets
                type_target = Promotion.p1_type
                id_target = Promotion.p1_id
            elif direction == "from":
                model_target = self.model.promoted_from_sources
                type_target = Promotion.p0_type
                id_target = Promotion.p0_id

            if promoted is not None:
                # if a tuple check for between
                if isinstance(promoted, tuple):
                    target_type0, target_id0 = _promotion_split(promoted[0])
                    target_type1, target_id1 = _promotion_split(promoted[1])
                    # make sure the types are the same otherwise error out
                    if target_type0 != target_type1:
                        raise TypeError(f"{filter_target} types are not the same")
                    query = query.join(model_target).\
                        filter(type_target == target_type0).\
                        filter(id_target.between(target_id0, target_id1))
                # if a list get every item
                elif isinstance(promoted, list):
                    target_type = None
                    target_ids = []
                    for item in promoted:
                        _type, _id = _promotion_split(item)
                        # check to make sure all types are the same
                        if target_type is None:
                            target_type = _type
                        elif target_type != _type:
                            raise TypeError(f"{filter_target} types are not the same")
                        target_ids.append(_id)
                    if target_ids != []:
                        query = query.join(model_target).\
                            filter(type_target == target_type).\
                            filter(id_target.in_(target_ids))
                else:
                    target_type, target_id = _promotion_split(promoted)
                    if target_type is not None:
                        query = query.join(model_target)\
                            .filter(type_target == target_type)\
                            .filter(id_target == target_id)

            if not_promoted is not None:
                if isinstance(not_promoted, tuple):
                    target_type0, target_id0 = _promotion_split(not_promoted[0])
                    target_type1, target_id1 = _promotion_split(not_promoted[1])
                    if target_type0 != target_type1:
                        raise TypeError(f"{filter_target} types are not the same")
                    query = query.join(model_target).\
                        filter(type_target == target_type).\
                        filter(~id_target.between(target_id0, target_id1))
                elif isinstance(not_promoted, list):
                    target_type = None
                    target_ids = []
                    for item in not_promoted:
                        _type, _id = _promotion_split(item)
                        # check to make sure all types are the same
                        if target_type is None:
                            target_type = _type
                        elif target_type != _type:
                            raise TypeError(f"{filter_target} types are not the same")
                        target_ids.append(_id)
                    if target_ids != []:
                        query = query.join(model_target).\
                            filter(type_target == target_type).\
                            filter(id_target.not_in(target_ids))
                else:
                    target_type, target_id = _promotion_split(not_promoted)
                    if target_type is not None:
                        query = query.join(model_target)\
                            .filter(type_target == target_type)\
                            .filter(id_target != target_id)

        return query

    def _tag_or_source_filter(self, query: Query, filter_dict: dict, target_type: TargetTypeEnum):
        if target_type == TargetTypeEnum.tag:
            item = filter_dict.pop("tag", None)
            not_item = filter_dict.get("not", {}).pop("tag", None)
        elif target_type == TargetTypeEnum.source:
            item = filter_dict.pop("source", None)
            not_item = filter_dict.get("not", {}).pop("source", None)

        if item is not None or not_item is not None:
            # join to link table (in either direction)
            link_alias = aliased(Link)
            if target_type == TargetTypeEnum.tag:
                linked_table = aliased(Tag)
            elif target_type == TargetTypeEnum.source:
                linked_table = aliased(Source)

            # First links join
            query = query.outerjoin(
                link_alias,
                (
                    (self.model.target_type_enum() == link_alias.v0_type)
                    & (self.model.id == link_alias.v0_id)
                    & (target_type == link_alias.v1_type)
                )
            )
            # Join to target table
            query = query.outerjoin(
                linked_table, linked_table.id == link_alias.v1_id
            )

        if item is not None:
            if isinstance(item, tuple):
                query = query.filter(linked_table.name.between(item[0], item[1]))
            if isinstance(item, list):
                query = query.filter(linked_table.name.in_(item))
            else:
                query = query.filter(linked_table.name == item)

        if not_item is not None:
            if isinstance(not_item, tuple):
                query = query.filter(~linked_table.name.between(not_item[0], not_item[1]))
            if isinstance(not_item, list):
                query = query.filter(linked_table.name.not_in(not_item))
            else:
                query = query.filter(linked_table.name != not_item)

        return query

    def _json_filter(self, query: Query, filter_dict: dict, filter_key: str, json_field: str, model_attribute: str):
        if hasattr(self.model, model_attribute):
            value = filter_dict.pop(filter_key, None)
            not_value = filter_dict.get("not", {}).pop(filter_key, None)
            if value is not None or not_value is not None:
                model = getattr(self.model, model_attribute)

                if value is not None:
                    # does this even make sense? raise exception or just treat it like range?
                    if not isinstance(value, list) and not isinstance(value, tuple):
                        value = [value]

                    condition = []
                    for item in value:
                        if query.session.bind.dialect.name == "mysql":
                            condition.append(func.json_contains(model, f'"{item}"', f"$.{json_field}") == 1)
                        elif query.session.bind.dialect.name == "postgresql":
                            condition.append(model.contains({json_field: [item]}))
                        elif query.session.bind.dialect.name == "sqlite":
                            data_func = func.json_each(model, f"$.{json_field}").table_valued(
                                "value", joins_implicitly=True
                            )
                            condition.append(data_func.c.value == item)
                        else:
                            pass  # We don't support other database types with this filter
                    query = query.filter(or_(*condition))

                if not_value is not None:
                    # does this even make sense? raise exception or just treat it like range?
                    if not isinstance(not_value, list) and not isinstance(not_value, tuple):
                        not_value = [not_value]

                    condition = []
                    for item in not_value:
                        if query.session.bind.dialect.name == "mysql":
                            condition.append(func.json_contains(model, f'"{item}"', f"$.{json_field}") == 0)
                        elif query.session.bind.dialect.name == "postgresql":
                            condition.append(~model.contains({json_field: [item]}))
                        elif query.session.bind.dialect.name == "sqlite":
                            data_func = func.json_each(model, f"$.{json_field}").table_valued(
                                "value", joins_implicitly=True
                            )
                            condition.append(data_func.c.value != item)
                        else:
                            pass  # We don't support other database types with this filter
                    query = query.filter(and_(*condition))

        return query

    def filter(self, query: Query, filter_dict: dict):
        not_filter_dict = filter_dict.pop("not", {})
        # General case - put special cases in specific classes
        for key, item in filter_dict.items():
            # Ignore unknown and not set parameters
            if item is None:
                continue
            field = getattr(self.model, key, None)
            if field is None:
                continue
            if isinstance(item, tuple):
                # if the first item is a string then just do in_ searches
                if isinstance(item[0], str):
                    # if item is a list then find all items within
                    query = query.filter(field.in_(item))
                else:
                    # item is a tuple then do range searching
                    query = query.filter(field.between(item[0], item[1]))
            elif isinstance(item, list):
                # if item is a list then find all items within
                query = query.filter(field.in_(item))
            else:
                query = query.filter(field == item)

        # do negation filters
        for key, item in not_filter_dict.items():
            # Ignore unknown and not set parameters
            if item is None:
                continue
            field = getattr(self.model, key, None)
            if field is None:
                continue
            if isinstance(item, tuple):
                # if the first item is a string then just do in_ searches
                if isinstance(item[0], str):
                    # if item is a list then find all items within
                    query = query.filter(field.not_in(item))
                else:
                    # item is a tuple then do range searching
                    query = query.filter(~field.between(item[0], item[1]))
            elif isinstance(item, list):
                # if item is a list then find all items within
                query = query.filter(field.not_in(item))
            else:
                query = query.filter(field != item)

        return query

    def sort(self, query, sort_string):
        # Sort asc/desc based on specified attribute
        # String is none or empty
        if not sort_string:
            return query
        # Add + modifier if no directional modifier provided
        if sort_string[0] not in "+-":
            sort_string = "+" + sort_string
        sort_attribute = sort_string[1:]
        if hasattr(self.model, sort_attribute):
            if sort_string[0] == "+":
                return query.order_by(getattr(self.model, sort_attribute))
            else:
                return query.order_by(getattr(self.model, sort_attribute).desc())
        # We can't sort by that attribute
        else:
            raise ValueError("Cannot sort by attribute %s" % sort_attribute)

    def get_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        skip: int = 0,
        limit: int = 100,
        audit_logger=None,
    ):
        """
        Gets all objects using the specified roles, with limit and offset
        """
        result = (
            self.query_objects_with_roles(db_session, roles)
            .offset(skip)
            .limit(limit)
            .all()
        )
        if audit_logger is not None:
            for item in result:
                audit_logger.log("read", item, log_thing=False)
        return result

    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read,
    ):
        """
        This utility function returns a query on a subset of the given table
        which the user has access to by id
        Note that model MUST have an integer primary key
        Admins will always see everything.
        :param db_session:
        :param user:
        :param required_permission:
        :return:
        """
        # NOTE: This query always returns objects accessible to the
        # "everyone" role (usually role id 0)
        # Admin permissions need to be checked elsewhere
        model_primary_key = inspect(self.model).primary_key[0]
        query = db_session.query(self.model)

        return query.join(Permission, (model_primary_key == Permission.target_id))\
            .filter(((self.model.target_type_enum() == Permission.target_type)
                     & (required_permission == Permission.permission))
                    )\
            .filter(Permission.role_id.in_([role.id for role in roles]
                                           + [settings.EVERYONE_ROLE_ID]))\
            .distinct()

    def create_with_owner(
        self,
        db_session: Session,
        *,
        obj_in: Union[CreateSchemaType, dict[str, Any]],
        owner: User,
        audit_logger=None
    ) -> ModelType:
        # Check for CreateSchemaType (=__orig_bases__[0].__args__[1])
        if (isinstance(obj_in, self.__orig_bases__[0].__args__[1])
                and hasattr(obj_in, "owner")
                and "owner" not in obj_in.model_fields_set):
            obj_in.owner = owner.username
        if (isinstance(obj_in, dict)
                and "owner" not in obj_in):
            obj_in["owner"] = owner.username
        db_obj = self.create(db_session, obj_in=obj_in, audit_logger=audit_logger)
        tt = self.model.target_type_enum()
        if tt:
            from app.crud import permission

            permission.create_owner_permissions(
                db_session, owner, tt, db_obj.id, audit_logger=audit_logger
            )
        return db_obj

    def create_with_permissions(
        self,
        db_session: Session,
        *,
        obj_in: Union[CreateSchemaType, dict[str, Any]],
        perm_in: dict[PermissionEnum, list],
        audit_logger=None
    ) -> ModelType:
        """
        Create an object with initial permissions

        obj_in: The object to create
        perm_in: A dictionary of <Permission>: <role name/id>
        """
        if PermissionEnum.admin in perm_in:
            raise ValueError("Users cannot assign admin permissions")
        db_obj = self.create(db_session, obj_in=obj_in, audit_logger=audit_logger)
        tt = self.model.target_type_enum()
        # Assign permissions (if applicable)
        if tt is not None and tt != TargetTypeEnum.none:
            # need to import here to avoid circular dependency
            from app.crud import permission, role

            for perm in perm_in:
                new_perm = {
                    "permission": perm,
                    "target_type": tt,
                    "target_id": db_obj.id,
                }
                for r in perm_in[perm]:
                    role_id = r
                    if not isinstance(r, int):
                        role_id = role.get_role_by_name(db_session, r).id
                    new_perm["role_id"] = role_id
                    permission.create(
                        db_session, obj_in=new_perm, audit_logger=audit_logger
                    )
        return db_obj

    def create_in_object(
        self,
        db_session: Session,
        *,
        obj_in: Union[CreateSchemaType, dict[str, Any]],
        source_type: TargetTypeEnum,
        source_id: int,
        audit_logger=None
    ) -> ModelType:
        """
        Create a new object "inside" of another object, copying its permissions
        and creating a link between the parent and the child object.
        Permissions on the parent object should be checked before calling this
        method.
        """
        # Prevent circular dependency
        from app.crud import link, permission

        # for instances where self.model.target_type_enum() is None or TargetTypeEnum.none, should we still create the object or fail since we can't link with the other object
        new_obj = self.create(db_session, obj_in=obj_in, audit_logger=audit_logger)
        if self.model.target_type_enum() is not None and self.model.target_type_enum() != TargetTypeEnum.none:
            permission.copy_object_permissions(
                db_session,
                source_type,
                source_id,
                self.model.target_type_enum(),
                new_obj.id,
                audit_logger=audit_logger,
            )
            new_link = {
                "v1_type": self.model.target_type_enum(),
                "v1_id": new_obj.id,
                "v0_type": source_type,
                "v0_id": source_id,
                "weight": 1,
                "context": "Parent",
            }
            link.create(db_session, obj_in=new_link, audit_logger=audit_logger)
        return new_obj

    def get_history(self, db_session, id, only_latest_read=True):
        """
        Get the audit history of a particular object. By default only the latest
        and earliest 'read' audit is pulled for each user.
        """
        query = db_session.query(Audit).filter(
            (Audit.thing_type == self.model.target_type_enum().value)
            & (Audit.thing_id == id))
        if only_latest_read:
            subquery = db_session.query(
                Audit,
                func.row_number().over(
                    partition_by=[Audit.username, Audit.what], order_by=Audit.when_date.desc()
                ).label("row_number"),
                func.row_number().over(
                    partition_by=[Audit.username, Audit.what], order_by=Audit.when_date
                ).label("row_number_rev")
            )
            subquery = subquery.filter(
                (Audit.thing_type == self.model.target_type_enum().value)
                & (Audit.thing_id == id)
            ).subquery()
            audit_alias = aliased(Audit, subquery)
            query = db_session.query(audit_alias).filter(
                (subquery.c.row_number == 1)
                | (subquery.c.row_number_rev == 1)
                | (audit_alias.what != 'read')
            )
        return query.all()

    def undelete(
        self,
        db_session: Session,
        target_id: int | None = None,
        existing_data: Any | None = None,
        keep_ids: bool | None = True,
        by_user: str | None = None,
        audit_logger: Any | None = None,
    ):
        """
        Undeletes an object with id target_id. This object must have a delete
        operation recorded in the audit logs. If keep_ids is True, the object
        will be restored with the id it had previously. If multiple objects have
        been deleted with the same id, this only restores the most recent one to
        be deleted.
        """
        target_type = self.model.target_type_enum()
        # Check to see if an object with this id already exists
        if keep_ids and target_id is not None and db_session.get(self.model, target_id):
            raise ValueError(
                "An object with this id already exists (maybe it "
                "was already restored?). Set keep_ids to false if you "
                "want to recreate it under another id."
            )
        # Get latest deleted object with proper "what" string
        # Make this cleaner by cleaning up audit table?
        if existing_data is None:
            if target_id is None:
                raise ValueError("Must specify target id to restore")
            query = db_session.query(Audit).filter(
                (Audit.what == "delete")
                & (Audit.thing_type == target_type.value)
                & (Audit.thing_id == target_id)
            )
            if by_user is not None:
                query = query.filter(Audit.username == by_user)
            audit = query.order_by(Audit.when_date.desc()).first()
            if not audit:
                return None
            object_data = audit.audit_data
        else:
            object_data = existing_data
        # Extract special cases of object data
        # Entries
        if "entries" in object_data:
            from app.crud import entry

            for entry_object in object_data["entries"]:
                entry.undelete(
                    db_session,
                    existing_data=entry_object,
                    keep_ids=keep_ids,
                    audit_logger=audit_logger,
                )
        # Promotions
        if "promoted_from_sources" in object_data:
            from app.crud import promotion

            for promotion_object in object_data["promoted_from_sources"]:
                promotion.undelete(
                    db_session,
                    existing_data=promotion_object,
                    keep_ids=keep_ids,
                    audit_logger=audit_logger,
                )
        if "promoted_to_targets" in object_data:
            from app.crud import promotion

            for promotion_object in object_data["promoted_to_targets"]:
                promotion.undelete(
                    db_session,
                    existing_data=promotion_object,
                    keep_ids=keep_ids,
                    audit_logger=audit_logger,
                )
        # Tags and sources (assignment silently fails if tag/source no longer
        # exists)
        if "tags" in object_data:
            from app.crud import tag

            for tag_object in object_data["tags"]:
                tag.assign(
                    db_session,
                    target_type=target_type,
                    tag_id=tag_object["id"],
                    target_id=target_id,
                    audit_logger=audit_logger,
                )
        if "sources" in object_data:
            from app.crud import source

            for source_object in object_data["sources"]:
                source.assign(
                    db_session,
                    target_type=target_type,
                    source_id=source_object["id"],
                    target_id=target_id,
                    audit_logger=audit_logger,
                )
        # Restore simple attributes
        restored = self.model()
        columns = inspect(self.model).column_attrs
        for column in columns:
            # Don't set id unless keep_ids is True
            if column.key in object_data and (keep_ids or column.key != "id"):
                setattr(restored, column.key, object_data[column.key])
            # restore proper datetimes probably will need to add any other datetimes that come up
            if column.key in object_data and (
                column.key == "modified" or column.key == "created"
            ):
                setattr(restored, column.key, parse(object_data[column.key]))
        # Commit back to db
        db_session.add(restored)
        db_session.flush()
        if audit_logger is not None:
            audit_logger.log("undelete", restored)
        return restored

    @staticmethod
    def publish(action, uid=None, model=ModelType):
        for key in CRUDBase.global_subscribers.keys():
            CRUDBase.global_subscribers[key].append(
                {"action": action, "uid": uid, "model": model}
            )


if __name__ == "__main__":
    pass
