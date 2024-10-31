from typing import get_args
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase
from app.enums import TargetTypeEnum, PermissionEnum
from app.models import Event, Signature, Role, Permission, Link
from app.schemas.signature import SignatureCreate, SignatureUpdate


class CRUDSignature(CRUDBase[Signature, SignatureCreate, SignatureUpdate]):
    # Custom filtering for signatures
    def filter(self, query, filter_dict):
        query = self._str_filter(query, filter_dict, "name")
        query = self._str_filter(query, filter_dict, "description")
        query = self._json_filter(query, filter_dict, "signature_group", "signature_group", "data")
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.tag)
        query = self._tag_or_source_filter(query, filter_dict, TargetTypeEnum.source)

        return super().filter(query, filter_dict)

    def query_objects_with_roles(
        self,
        db_session: Session,
        roles: list[Role],
        required_permission: PermissionEnum = PermissionEnum.read,
    ):
        """
        Signatures have json fields, and so need a slightly different query
        Note: admin permissions must be checked elsewhere
        """
        query = (
            db_session.query(self.model)
            .join(Permission, (self.model.id == Permission.target_id))
            .filter(((self.model.target_type_enum() == Permission.target_type)
                     & (required_permission == Permission.permission))
                    )
            .filter(Permission.role_id.in_([role.id for role in roles]
                                           + [settings.EVERYONE_ROLE_ID]))
            .group_by(self.model.id)  # We can't use DISTINCT with signatures
        )
        return query

    def retrieve_signature_links(self, db_session: Session, signature_id: int):
        link_query_right = db_session.query(Link).filter(
            and_(Link.v1_id == signature_id, Link.v1_type == TargetTypeEnum.signature)
        )
        link_query_left = db_session.query(Link).filter(
            and_(Link.v0_id == signature_id, Link.v0_type == TargetTypeEnum.signature)
        )
        signature_links = link_query_left.union(link_query_right).all()

        element_dict = {
            TargetTypeEnum.alert: [],
            TargetTypeEnum.event: [],
            TargetTypeEnum.intel: [],
            TargetTypeEnum.dispatch: [],
            TargetTypeEnum.product: [],
            TargetTypeEnum.incident: [],
            TargetTypeEnum.signature: []
        }

        for signature_link in signature_links:
            if signature_link.v0_type == TargetTypeEnum.signature:
                if element_dict.get(signature_link.v1_type) is not None:
                    element_dict[signature_link.v1_type].append(signature_link.v1_id)
            else:
                if element_dict.get(signature_link.v0_type) is not None:
                    element_dict[signature_link.v0_type].append(signature_link.v0_id)

        appearances = []
        for element_type, element_ids in element_dict.items():
            # We want to get the alerts (with the alertgroup subject), events, intels, dispatches, products, incidents, or signatures.
            # Get model as first generic parameter of crud type (mapped from target type)
            model = get_args(self.target_crud_mapping[element_type].__orig_bases__[0])[0]
            db_objs = db_session.query(model).filter(model.id.in_(element_ids)).all()
            for appearance in db_objs:
                appearance_dict = {
                    "id": appearance.id,
                    "type": element_type,
                    "last_updated": appearance.modified,
                    "status": appearance.status
                }
                if element_type == TargetTypeEnum.alert:
                    appearance_dict["subject"] = appearance.alertgroup_subject
                elif element_type == TargetTypeEnum.signature:
                    appearance_dict["subject"] = appearance.name
                else:
                    appearance_dict["subject"] = appearance.subject
                appearances.append(appearance_dict)
        return appearances, len(appearances)

    def get_event_owner_stats(self, db_session: Session, signature_id: int):
        link_query_right = db_session.query(Link).filter(
            and_(Link.v1_id == signature_id, Link.v1_type == TargetTypeEnum.signature)
        )
        link_query_left = db_session.query(Link).filter(
            and_(Link.v0_id == signature_id, Link.v0_type == TargetTypeEnum.signature)
        )
        signature_links = link_query_left.union(link_query_right).all()

        event_ids = []
        for signature_link in signature_links:
            if signature_link.v0_type == TargetTypeEnum.signature:
                event_ids.append(signature_link.v1_id)
            else:
                event_ids.append(signature_link.v0_id)

        # Now get all the IDS
        linked_events = db_session.query(Event.owner, func.count(Event.owner)).filter(Event.id.in_(event_ids)).group_by(Event.owner).all()
        return [{"owner": x[0], "count": x[1]} for x in linked_events]

    # def get_alert_stats(self, db_session=None, signature_id=None):
    #     signature_links = db_session.query(Link.v0_id, Link.v0_type, Link.v1_id, Link.v1_type).filter(or_(and_(Link.v1_id == signature_id, Link.v1_type == TargetTypeEnum.signature, Link.v0_type == TargetTypeEnum.alert), and_(Link.v0_id == signature_id, Link.v0_type == TargetTypeEnum.signature, Link.v1_type == TargetTypeEnum.alert))).all()
    #     alert_ids = []
    #     for signature_link in signature_links:
    #         if signature_link[1] == TargetTypeEnum.signature:
    #             alert_ids.append(signature_link[2])
    #         else:
    #             alert_ids.append(signature_link[0])
    #     # Now get all the IDS
    #     entity_links = db_session.query(Link.v0_id, Link.v0_type, Link.v1_id, Link.v1_type).filter(or_(and_(Link.v1_id.in_(alert_ids), Link.v1_type == TargetTypeEnum.alert, Link.v0_type == TargetTypeEnum.entity), and_(Link.v0_id.in_(alert_ids), Link.v0_type == TargetTypeEnum.alert, Link.v1_type == TargetTypeEnum.entity))).all()
    #     alert_entity_map = {}
    #     entity_ids = set([])
    #     for entity_link in entity_links:
    #         if entity_link[1] == TargetTypeEnum.alert:
    #             if alert_entity_map.get(entity_link[0]) is None:
    #                 alert_entity_map[entity_link[0]] = []
    #             alert_entity_map[entity_link[0]].append(entity_link[2])
    #             entity_ids.add(entity_link[2])
    #         else:
    #             if alert_entity_map.get(entity_link[2]) is None:
    #                 alert_entity_map[entity_link[2]] = []
    #             alert_entity_map[entity_link[2]].append(entity_link[0])
    #             entity_ids.add(entity_link[0])
    #     entity_values = {x[0]: x[1] for x in db_session.query(Entity.id, Entity.value).filter(Entity.id.in_(entity_ids)).all()}
    #     linked_alerts = db_session.query(Alert.status, Alert.created, Alert.modified, Alert.id).filter(Alert.id.in_(alert_ids)).all()
    #     stats = {"promoted_count": 0, "closed_count": 0, "open_count": 0, "total_count": len(linked_alerts), "promoted_entity_value_counts": Counter({}), "closed_entity_value_counts": Counter({}), "open_entity_value_counts": Counter({}), "total_entity_value_counts": Counter({}), "promoted_rate": -1, "closed_rate": -1, "open_rate": -1, "last_promoted_alert_date": pytz.UTC.localize(datetime.datetime.min).timestamp(), "last_created_alert_date": pytz.UTC.localize(datetime.datetime.min).timestamp(), "created_time_series": [], "promoted_time_series": []}
    #     for linked_alert in linked_alerts:
    #         entity_value_counts = Counter([entity_values[x] for x in alert_entity_map[linked_alert[3]]])
    #         stats["created_time_series"].append(linked_alert[2].timestamp())
    #         if stats['last_created_alert_date'] < linked_alert[1].timestamp():
    #             stats['last_created_alert_date'] = linked_alert[1].timestamp()
    #         if linked_alert[0] == StatusEnum.promoted:
    #             stats['promoted_count'] += 1
    #             stats["promoted_time_series"].append(linked_alert[2].timestamp())
    #             if stats['last_promoted_alert_date'] < linked_alert[1].timestamp():
    #                 stats['last_promoted_alert_date'] = linked_alert[1].timestamp()
    #             stats['promoted_entity_value_counts'] += entity_value_counts
    #         elif linked_alert[0] == StatusEnum.closed:
    #             stats['closed_count'] += 1
    #             stats['closed_entity_value_counts'] += entity_value_counts
    #         elif linked_alert[0] == StatusEnum.open:
    #             stats['open_count'] += 1
    #             stats['open_entity_value_counts'] += entity_value_counts
    #         stats['total_entity_value_counts'] += entity_value_counts
    #     if stats['total_count'] != 0:
    #         stats['promoted_rate'] = stats['promoted_count'] / stats['total_count']
    #         stats['closed_rate'] = stats['closed_count'] / stats['total_count']
    #         stats['open_rate'] = stats['closed_count'] / stats['total_count']
    #
    #     return stats

    # def update_signature_stats(self, signature_id=None, db_session=None, audit_logger=None):
    #     signature = db_session.query(Signature).filter(Signature.id == signature_id).one()
    #     alert_stats = self.get_alert_stats(db_session=db_session, signature_id=signature.id)
    #     return self.update(db_session=db_session, db_obj=signature, obj_in={"stats": {"alert_stats": alert_stats}}, audit_logger=audit_logger)

    # def sort_by_stat_rankings(self, signature_id=None, db_session=None, audit_logger=None):
    #     # How does this signature statistics compare globally
    #     signatures = db_session.query(Signature.id, Signature.stats).all()
    #     total_signatures = len(signatures)
    #     stats_table = [{"id": x[0], "total_count": x[1]["alert_stats"]["total_count"], "promoted_count": x[1]["alert_stats"]["promoted_count"], "open_count":x[1]["alert_stats"]["open_count"], "closed_count": x[1]["alert_stats"]["closed_count"], "promoted_rate":x[1]["alert_stats"]["promoted_rate"], "open_rate":x[1]["alert_stats"]["open_rate"], "closed_rate":x[1]["alert_stats"]["closed_rate"]} for x in signatures if (x[1] is not None and x[1].get("alert_stats") is not None)]
    #     df = pd.DataFrame.from_records(stats_table)
    #     df.sort_values(by=['total_count'], inplace=True)


signature = CRUDSignature(Signature)
