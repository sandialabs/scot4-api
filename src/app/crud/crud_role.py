from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate
from app.schemas.setting import AuthSettings


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def get_role_by_name(
        self, db_session: Session, name: str, audit_logger=None
    ) -> Role | None:
        query = db_session.query(self.model).filter(self.model.name == name)
        result = query.first()
        if audit_logger is not None:
            audit_logger.log("read", result, log_thing=False)
        return result

    def ensure_roles_on_user(
        self,
        db_session: Session,
        user: User,
        role_names: list[str],
        auth_method: AuthSettings = None,
        create: bool = False,
        audit_logger=None,
    ):
        """
        Ensure that the given user has all of the roles specified (by name)
        If an auth method is given also *removes* all roles managed by that auth
                method that aren't in the list of role names and associates all
                given roles with that auth method.
        Returns True if the user's roles were modified, False otherwise
        """
        user_role_names = [r.name for r in user.roles]
        new_roles = []
        # Find the role object for all roles to be added to the user
        for role_name in role_names:
            if role_name not in user_role_names:
                role_add = self.get_role_by_name(db_session, role_name)
                if role_add is None and create:
                    role_add = self.create(
                        db_session,
                        obj_in=RoleCreate(name=role_name),
                        audit_logger=audit_logger,
                    )
                if role_add:
                    new_roles.append(role_add)
        # If auth method given, associate roles with this auth
        if auth_method:
            auth_role_names = set(r.name for r in auth_method.linked_roles)
            roles_add_to_auth = set(
                rname for rname in role_names if rname not in auth_role_names
            )
            auth_role_names.update(roles_add_to_auth)
            # Add roles we already looked up in new_roles
            for role_add in new_roles:
                if role_add.name in roles_add_to_auth:
                    auth_method.linked_roles.append(role_add)
                    roles_add_to_auth.remove(role_add.name)
            # Add roles that weren't in new_roles
            for role_add_name in roles_add_to_auth:
                r = self.get_role_by_name(db_session, role_add_name)
                if r:
                    auth_method.linked_roles.append(r)
            # Finally, delete roles from user that are managed by this auth
            # method, but not in the list of assigned roles
            for current_role in user.roles:
                if current_role.name in auth_role_names and not (
                    current_role.name in role_names
                ):
                    user.roles.remove(current_role)
        if new_roles:
            for new_role in new_roles:
                # Log role assignment
                if audit_logger is not None:
                    audit_logger.log("assign " + user.username, new_role)
            user.roles.extend(new_roles)
            db_session.add(user)
            db_session.flush()
            return True
        else:
            return False


role = CRUDRole(Role)
