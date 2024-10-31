from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.enums import TargetTypeEnum
from app.models.link import Link
from app.schemas.link import LinkCreate, LinkUpdate


class CRUDLink(CRUDBase[Link, LinkCreate, LinkUpdate]):
    def delete_links(
        self,
        db_session: Session,
        target_type_1: TargetTypeEnum,
        target_id_1: int,
        target_type_2: TargetTypeEnum,
        target_id_2: int,
        bidirectional: bool = True,
        audit_logger=None,
    ):
        """
        Deletes all links between the two target objects; if bidirectional is true,
        also deletes all links going the other direction as well.
        """
        query = db_session.query(self.model)
        if bidirectional:
            query = query.filter(
                (
                    (Link.v0_type == target_type_1)
                    & (Link.v0_id == target_id_1)
                    & (Link.v1_type == target_type_2)
                    & (Link.v1_id == target_id_2)
                )
                | (
                    (Link.v1_type == target_type_1)
                    & (Link.v1_id == target_id_1)
                    & (Link.v0_type == target_type_2)
                    & (Link.v0_id == target_id_2)
                )
            )
        else:
            query = query.filter(
                (Link.v0_type == target_type_1)
                & (Link.v0_id == target_id_1)
                & (Link.v1_type == target_type_2)
                & (Link.v1_id == target_id_2)
            )
        links_to_delete = query.all()
        if not links_to_delete:
            return None
        else:
            for link in links_to_delete:
                if audit_logger is not None:
                    audit_logger.log("delete", link)
                db_session.delete(link)
            db_session.flush()
            return links_to_delete

    def delete_links_for_object(
        self,
        db_session: Session,
        target_type: TargetTypeEnum,
        target_id: int,
        audit_logger=None,
    ):
        """
        Deletes all links to or from the target object
        """
        query = db_session.query(self.model).filter(
            ((Link.v0_type == target_type) & (Link.v0_id == target_id))
            | ((Link.v1_type == target_type) & (Link.v1_id == target_id))
        )
        links_to_delete = query.all()
        if not links_to_delete:
            return None
        else:
            for link in links_to_delete:
                if audit_logger is not None:
                    audit_logger.log("delete", link)
                db_session.delete(link)
            db_session.flush()
            return links_to_delete


link = CRUDLink(Link)
