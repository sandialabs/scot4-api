from typing import Union
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.crud.base import CRUDBase
from app.enums import PermissionEnum, TargetTypeEnum
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.schemas.permission import PermissionCreate, PermissionUpdate


class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    def get_permissions_from_roles(
        self,
        db: Session,
        roles: list[Role],
        target_type: TargetTypeEnum,
        target_id: int | None = None,
    ):
        """
        Gets this list of roles' effective permissions on an object with type
        target_type and id target_id (or on any object if no target_id is given)
        NOTE: This includes all permissions from the "everyone" role, which all
        users implicitly have.
        """
        query = db.query(Permission.permission)\
            .filter(Permission.target_type == target_type)
        if target_id is not None:
            query = query.filter(Permission.target_id == target_id)
        query = (
            query.join(Role)
            .filter(Role.id.in_([r.id for r in roles] + [settings.EVERYONE_ROLE_ID]))
            .distinct()
        )
        final_permissions = [p.permission for p in query.all()]
        # Query for admin role separately - more performant
        if target_type != TargetTypeEnum.admin:
            admin_role = db.query(Role).join(Permission)\
                .filter((Permission.permission == PermissionEnum.admin)
                        & (Permission.target_type == TargetTypeEnum.admin)
                        & (Role.id.in_([r.id for r in roles]
                                       + [settings.EVERYONE_ROLE_ID]))
                        )\
                .first()
            if admin_role:
                final_permissions.append(PermissionEnum.admin)
        return final_permissions

    def get_permissions(
        self,
        db: Session,
        username: str,
        target_type: TargetTypeEnum,
        target_id: int | None = None,
    ):
        """
        Query a user's effective permission on an object
        If target_id is None, will query for permissions on any id.
        An empty list will be returned if the object doesn't exist.
        """
        query = db.query(Permission.permission).filter(
            Permission.target_type == target_type
        )
        if target_id is not None:
            query = query.filter(Permission.target_id == target_id)
        # NOTE: The "everyone" role is included in the user's effective roles
        query = (
            query.join(
                Role,
                (Permission.role_id == Role.id)
                | (Permission.role_id == settings.EVERYONE_ROLE_ID),
            )
            .join(User, Role.users)
            .filter(User.username == username)
            .distinct()
        )
        final_permissions = [p.permission for p in query.all()]
        # Query for admin role separately - more performant
        if target_type != TargetTypeEnum.admin and self.user_is_admin(db, username):
            final_permissions.append(PermissionEnum.admin)
        return final_permissions

    def user_is_admin(self, db: Session, user: Union[User, str]):
        if isinstance(user, User):
            user = user.username
        admin_role = db.query(User).join(Role, User.roles).join(
            Permission,
            (Permission.role_id == Role.id)
            | (Permission.role_id == settings.EVERYONE_ROLE_ID)
        )\
            .filter((Permission.permission == PermissionEnum.admin)
                    & (Permission.target_type == TargetTypeEnum.admin)
                    & (User.username == user)
                    )\
            .first()
        return admin_role is not None

    def roles_have_admin(self, db: Session, roles: list[Role] | None):
        if roles is None:
            return False
        selected_admin_role = db.query(Role).join(Permission).filter(
            (Permission.permission == PermissionEnum.admin)
            & (Permission.target_type == TargetTypeEnum.admin)
            & (Role.id.in_([r.id for r in roles]))
        ).first()
        if selected_admin_role is not None:
            return True
        return False

    def grant_permission(
        self, db: Session, permission_create: PermissionCreate, audit_logger=None
    ):
        db_permission = (
            db.query(Permission)
            .filter(
                (Permission.role_id == permission_create.role_id)
                & (Permission.target_type == permission_create.target_type)
                & (Permission.target_id == permission_create.target_id)
                & (Permission.permission == permission_create.permission)
            )
            .first()
        )
        if db_permission:
            if audit_logger is not None:
                audit_logger.log("read", db_permission, log_thing=False)
            return db_permission
        else:
            # check if target_id exists before granting permission except for admin targets
            if permission_create.target_type != TargetTypeEnum.admin:
                _target_model = self.target_crud_mapping[permission_create.target_type]
                if not _target_model.get(db, permission_create.target_id):
                    raise ValueError(f"Target Type {permission_create.target_type} with {permission_create.target_id} not found")

            new_permission = self.create(db, obj_in=permission_create)
            if audit_logger is not None:
                audit_logger.log("create", new_permission)
            return new_permission

    def revoke_permission(
        self, db: Session, permission_revoke: PermissionCreate, audit_logger=None
    ):
        db_permission = (
            db.query(Permission)
            .filter(
                (Permission.role_id == permission_revoke.role_id)
                & (Permission.target_type == permission_revoke.target_type)
                & (Permission.target_id == permission_revoke.target_id)
                & (Permission.permission == permission_revoke.permission)
            )
            .first()
        )
        if not db_permission:
            return None
        if audit_logger is not None:
            audit_logger.log("delete", db_permission)
        db.delete(db_permission)
        db.flush()
        return db_permission

    def create_owner_permissions(
        self,
        db: Session,
        owner: User,
        target_type: TargetTypeEnum,
        target_id: int | None = None,
        audit_logger=None,
    ):
        """
        Create initial permissions on an object when someone creates it
        The initial permissions are a mix of the global default settings and
        whatever the user has set as default settings in their preferences
        If there are no default permissions, the "everyone" role is used
        """
        default_role = None
        global_settings = crud.setting.get(db)
        default_permissions = {}
        if global_settings.default_permissions:
            default_permissions = global_settings.default_permissions.get("default", {})
            default_permissions.update(global_settings.default_permissions.get(target_type.value, {}))
        # Users can override global default permissions in their preferences
        user_defaults = None
        if owner.preferences:
            user_defaults = owner.preferences.get("default_permissions")
        if user_defaults:
            default_permissions.update(user_defaults.get("default", {}))
            default_permissions.update(user_defaults.get(target_type.value, {}))
        for permission in [
            PermissionEnum.read,
            PermissionEnum.modify,
            PermissionEnum.delete,
        ]:
            permission_role_ids = default_permissions.get(permission.value, [])
            # If there's no default roles set, add the default "everyone" role
            # The user should already have this role implicitly
            if not permission_role_ids:
                # Default role is the role with id 0 (special case)
                if not default_role:
                    default_role = crud.role.get(db, settings.EVERYONE_ROLE_ID)
                # If we can't find the default role, just give up
                if default_role:
                    permission_role_ids.append(default_role.id)
            # Add permissions to all roles which had this permission on at least
            # one other object
            for role_id in permission_role_ids:
                add_perm = Permission(
                    role_id=role_id,
                    target_type=target_type,
                    target_id=target_id,
                    permission=permission,
                )
                db.add(add_perm)
                if audit_logger is not None:
                    audit_logger.log("create", add_perm)
        db.flush()

    def get_permission_roles(
        self, db: Session, target_type: TargetTypeEnum, target_id: int
    ):
        """
        Query which roles have any permission on a particular object
        Returns an empty dictionary if the object does not exist
        """
        permission_roles = (
            db.query(Permission.permission, Role)
            .filter(Permission.role_id == Role.id)
            .filter(Permission.target_id == target_id)
            .filter(Permission.target_type == target_type)
            .all()
        )
        result = {}
        for perm, role in permission_roles:
            if perm not in result:
                result[perm] = []
            result[perm].append(role)
        return result

    def copy_object_permissions(
        self,
        db: Session,
        source_type: TargetTypeEnum,
        source_id: int,
        target_type: TargetTypeEnum,
        target_id: int,
        audit_logger=None,
    ):
        """
        Copy all permissions from the source object to the target object.
        These permissions will be applied in addition to any it already has.
        """
        permission_roles = self.get_permission_roles(db, source_type, source_id)
        if permission_roles:
            for permission in permission_roles:
                for role in permission_roles[permission]:
                    new_permission = Permission(
                        role_id=role.id,
                        target_type=target_type,
                        target_id=target_id,
                        permission=permission,
                    )
                    db.add(new_permission)
                    if audit_logger is not None:
                        audit_logger.log("create", new_permission)
            db.flush()
        else:
            # Copy over the default permissions
            default_role = crud.role.get(db, settings.EVERYONE_ROLE_ID)
            if default_role:
                for permission in [PermissionEnum.read, PermissionEnum.modify, PermissionEnum.delete]:
                    add_perm = Permission(
                        role_id=default_role.id,
                        target_type=target_type,
                        target_id=target_id,
                        permission=permission,
                    )
                    db.add(add_perm)
                    if audit_logger is not None:
                        audit_logger.log("create", add_perm)
            db.flush()

    def filter_search_hits(
        self,
        db: Session,
        target_pairs: list[dict],
        roles: list[Role],
        audit_logger=None,
    ):
        """
        Filter search hits based on what the user can read.
        """
        if roles is not None:
            selected_admin_role = db.query(Role).join(Permission)\
                .filter((Permission.permission == PermissionEnum.admin)
                        & (Permission.target_type == TargetTypeEnum.admin)
                        & (Role.id.in_([r.id for r in roles])))\
                .first()
            if selected_admin_role is not None or len(target_pairs) == 0:
                return False
            else:
                query = db.query(Permission.target_type, Permission.target_id)
                conditionExpression = None
                for x in target_pairs:
                    if conditionExpression is None:
                        conditionExpression = ((Permission.target_type == x['type'])
                                               & (Permission.target_id == x['id']))
                    else:
                        conditionExpression = conditionExpression | (
                            (Permission.target_type == x['type'])
                            & (Permission.target_id == x['id'])
                        )
                query = query.filter((Permission.permission == PermissionEnum.read)
                                     & (Permission.role_id.in_([r.id for r in roles]))
                                     & (conditionExpression))

                return query.all()


permission = CRUDPermission(Permission)
