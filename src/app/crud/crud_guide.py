from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase
from app.models import Guide, Role, Permission, Signature, Link, User
from app.enums import TargetTypeEnum, PermissionEnum
from app.schemas.guide import GuideCreate, GuideUpdate
from app.crud.crud_signature import signature
from app.crud.crud_permission import permission


class CRUDGuide(CRUDBase[Guide, GuideCreate, GuideUpdate]):
    # Subject is filtered by string fragment
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "subject")

        return super().filter(query, filter_dict)

    def get_signatures_for(
        self,
        db_session: Session,
        guide_id: int,
        roles: list[Role] = None
    ):
        guide = self.get(db_session, guide_id)
        if not guide:
            return None
        if roles is None or permission.roles_have_admin(db_session, roles):
            query = db_session.query(Signature)
        else:
            query = signature.query_objects_with_roles(db_session, roles)
        query = query.join(Link, (Link.v0_id == Signature.id)
                           & (Link.v0_type == TargetTypeEnum.signature)
                           & (Link.v1_id == guide_id)
                           & (Link.v1_type == TargetTypeEnum.guide))
        return query.all()

    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read
    ):
        """
        Guides have json fields, and so need a slightly different query
        Note: admin permissions must be checked elsewhere
        """
        return db_session.query(self.model)\
            .join(Permission, (self.model.id == Permission.target_id))\
            .filter(((self.model.target_type_enum() == Permission.target_type) & (required_permission == Permission.permission)))\
            .filter(Permission.role_id.in_([role.id for role in roles] + [settings.EVERYONE_ROLE_ID]))\
            .group_by(self.model.id)  # We can't use DISTINCT with guides


guide = CRUDGuide(Guide)
