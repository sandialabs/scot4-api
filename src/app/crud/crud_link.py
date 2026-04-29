from sqlalchemy import func
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

    def find_all_links(self, db_session: Session, target_type: TargetTypeEnum, target_id: int):
        """
        Finds all links to or from the target object
        """
        return db_session.query(self.model).filter(
            ((Link.v0_type == target_type) & (Link.v0_id == target_id))
            | ((Link.v1_type == target_type) & (Link.v1_id == target_id))
        ).all()
    
    def target_filter(self, db_session: Session, target_ids: list[int], v1_type: TargetTypeEnum, v0_types: list[TargetTypeEnum] | None = None, and_: bool = False, skip: int = 0, limit: int | None = None, sort_string: str = None):
        """
        Finds all links with that either contain all target ids and a target type
        or if any link has any target ids and target type returns a list of targets with a list
        of matching item ids
        """
        query = db_session.query(Link.v0_id, Link.v0_type).filter((Link.v1_type == v1_type) & (Link.v1_id.in_(target_ids)))
        if v0_types is not None:
            # find specific target types if the ids are in the v1 columns
            query = query.filter((Link.v0_type.in_(v0_types)))
        
        query = query.group_by(*[Link.v0_id, Link.v0_type])

        # the total count doesn't work very well with the "and"
        count = self.get_count_from_query(query)
        if count is None:
            count = 0

        # if we want to return only the items that contain the list of ids match count to length of ids being looked up
        if and_:
            query = query.having(func.count(Link.v1_id).label("count") == len(target_ids))

        # Sort if sort string provided
        if sort_string is not None:
            # fix sorting from front end
            if "target_type" in sort_string:
                sort_string = sort_string.replace("target_type", "v0_type")
            if "target_id" in sort_string:
                sort_string = sort_string.replace("target_id", "v0_id")
                
            query = self.sort(query, sort_string)

        if limit and limit < 0:
            limit = None
        if skip and skip > 0:
            query = query.offset(skip)
        
        query = query.limit(limit)
        # union all queries together and return a list of targets with a list of all other associated targets
        results = []
        target_model = self.model.get_model_by_target_type(v1_type)
        for link in query.all():
            items = db_session.query(target_model).join(Link, (target_model.id == Link.v1_id))\
                .filter(Link.v0_id == link.v0_id)\
                .filter(Link.v0_type == link.v0_type)\
                .filter(Link.v1_type == v1_type).all()

            results.append({
                "target_type": link.v0_type,
                "target_id": link.v0_id,
                "items": items
            })

        return results, count
    
    def target_types(self, db_session: Session, target_ids: list[int], v1_type: TargetTypeEnum) -> dict[TargetTypeEnum, int]:
        """
        Finds all links with that either contain all target ids and a target type
        or if any link has any target ids and target type returns a list of targets with a list
        of matching item ids
        """
        data = {}
        for target in db_session.query(Link.v0_type, func.count(Link.v0_type).label("count")).filter((Link.v1_type == v1_type) & (Link.v1_id.in_(target_ids))).group_by(Link.v0_type).all():
            data[target.v0_type] = target.count

        return data


link = CRUDLink(Link) 
