import random
from faker import Faker
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.enums import TargetTypeEnum
from app import schemas, crud
from app.core.config import settings

from alertgroup import create_random_alertgroup
from apikey import create_apikey
from audit import create_audit
from appearance import create_random_appearance
from checklist import create_random_checklist
from dispatch import create_random_dispatch
from entity import create_random_entity
from event import create_random_event
from entry import create_random_entry
from feed import create_random_feed
from file import create_random_file
from flair import create_random_remote_flair
from game import create_random_game
from guide import create_random_guide
from handler import create_random_handler
from incident import create_random_incident
from index_search import index_search_results
from intel import create_random_intel
from link import create_link
from notification import create_random_notification
from permission import create_random_permission
from popularity import create_random_popularity
from product import create_random_product
from promotion import promote_alert_to_event, promote_dispatch_to_intel, promote_event_to_incident
from roles import create_random_role
from settings import create_random_setting
from sigbody import create_random_sigbody
from signature import create_random_signature
from source import create_random_source
from scot_stat import create_random_stat
from tag import create_random_tag
from threat_model_item import create_random_threat_model_item
from user_links import create_random_user_links
from user import create_user_with_role
from vuln_feed import create_random_vuln_feed
from vuln_track import create_random_vuln_track


def create_popularity(db: Session, faker: Faker, target_id: int, target_type: TargetTypeEnum, users: list[schemas.User]):
    for user in users:
        create_random_popularity(db, faker, target_type, target_id, owner=user)


def main() -> None:
    logger.info("Create initial data")
    db_session = SessionLocal()
    init_db(db_session, True, True, True)
    faker = Faker()
    try:
        saved_roles = []
        logger.info("Generating Roles")
        for _ in range(5):
            role = create_random_role(db_session, faker)
            saved_roles.append(role)
            logger.info(f"Role {role.name} Created")

        logger.info("Generating Users")
        users = [crud.user.get_by_username(db_session, username=settings.FIRST_SUPERUSER_USERNAME)]
        for _ in range(5):
            user = create_user_with_role(db_session, random.choice(saved_roles), faker)
            # create some api keys
            logger.debug(f"Creating User {user.email} API Key")
            create_apikey(db_session, faker, user)
            # make user a handler?
            if faker.pybool():
                create_random_handler(db_session, faker, user.username)
                logger.debug(f"User {user.email} is now a incident handler")

            users.append(user)
            logger.info(f"User {user.email} Created")

        setting = create_random_setting(db_session, faker)
        logger.info(f"Generated Site Setting {setting.id}")

        logger.info("Generate Signatures")
        # The idea here is to generate signatures that are going to
        # subsequently be tied to alertgroups that are generated.
        # i.e. a splunk saved search that is going to produce or already has produced alerts.
        signatures = []
        signature_names_types = []
        unique_signature_types = set(["None"])
        for _ in range(5):
            signature = create_random_signature(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, signature.id, TargetTypeEnum.signature, users)
            create_random_user_links(db_session, faker, signature.id, TargetTypeEnum.signature, random.choice(users))
            logger.info(f"Generating Random Entries for Signature {signature.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.signature, target_id=signature.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            signature_body = create_random_sigbody(db_session, faker, signature.id)
            logger.debug(f"Generated Random Signature Body {signature_body.id} for Signature {signature.id}")
            # Link a guide to a random threat model item
            signatures.append(signature)
            signature_names_types.append({"name": signature.name, "type": signature.type})
            unique_signature_types.add(signature.type)
            logger.debug(f"Generating Random Appearance for Signature {signature.id}")
            create_random_appearance(db_session, faker, signature.id, TargetTypeEnum.signature)
            logger.debug(f"Generating Random Source for Signature {signature.id}")
            create_random_source(db_session, faker, TargetTypeEnum.signature, signature.id)
            logger.debug(f"Generating Random Tag for Signature {signature.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.signature, signature.id)
            logger.debug(f"Generating Random Entity for Signature {signature.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.signature, signature.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.info(f"Signature {signature.id} Created")

        unique_signature_types = list(unique_signature_types)

        logger.info("Generating Alert Groups")
        for _ in range(5):
            alertgroup = create_random_alertgroup(db_session, signature_names_types, unique_signature_types, faker)
            create_popularity(db_session, faker, alertgroup.id, TargetTypeEnum.alertgroup, users)
            create_random_user_links(db_session, faker, alertgroup.id, TargetTypeEnum.alertgroup, random.choice(users))

            for alert in alertgroup.alerts:
                if faker.pybool():
                    logger.debug(f"Promoting Alert {alert.id}")
                    promote_alert_to_event(db_session, [alert.id])

                    if faker.pybool():
                        logger.debug(f"Promoting Alert TWICE {alert.id}")
                        promote_alert_to_event(db_session, [alert.id])

            logger.debug(f"Generating Random Appearance for Alert Group {alertgroup.id}")
            create_random_appearance(db_session, faker, alertgroup.id, TargetTypeEnum.alertgroup)
            logger.debug(f"Generating Random Source for Alert Group {alertgroup.id}")
            create_random_source(db_session, faker, TargetTypeEnum.alertgroup, alertgroup.id)
            logger.debug(f"Generating Random Tag for Alert Group {alertgroup.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.alertgroup, alertgroup.id)
            logger.debug(f"Generating Random Entity for Alert Group {alertgroup.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.alertgroup, alertgroup.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Alert Group {alertgroup.id}")
            create_random_permission(db_session, random.choice(saved_roles), alertgroup)
            logger.info(f"Alert Group {alertgroup.id} Created")

        logger.info("Generating Events")
        for _ in range(5):
            event = create_random_event(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, event.id, TargetTypeEnum.event, users)
            create_random_user_links(db_session, faker, event.id, TargetTypeEnum.event, random.choice(users))

            if faker.pybool():
                logger.debug(f"Promoting Event {event.id}")
                promote_event_to_incident(db_session, [event.id])

                if faker.pybool():
                    logger.debug(f"Promoting Event TWICE {event.id}")
                    promote_event_to_incident(db_session, [event.id])

            logger.info(f"Generating Random Entries for Event {event.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.event, target_id=event.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry)
            logger.debug(f"Generating Random Appearance for Event {event.id}")
            create_random_appearance(db_session, faker, event.id, TargetTypeEnum.event)
            logger.debug(f"Generating Random Source for Event {event.id}")
            create_random_source(db_session, faker, TargetTypeEnum.event, event.id)
            logger.debug(f"Generating Random Tag for Event {event.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.event, event.id)
            logger.debug(f"Generating Random Entity for Event {event.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.event, event.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Event {event.id}")
            create_random_permission(db_session, random.choice(saved_roles), event)
            logger.info(f"Event {event.id} Created")

        logger.info("Generating Vulnerability Queues")
        for _ in range(5):
            vuln_feed = create_random_vuln_feed(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, vuln_feed.id, TargetTypeEnum.vuln_feed, users)
            create_random_user_links(db_session, faker, vuln_feed.id, TargetTypeEnum.vuln_feed, random.choice(users))
            logger.info(f"Generating Random Entries for Vulnerability Queues {vuln_feed.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.vuln_feed, target_id=vuln_feed.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Vulnerability Queues {vuln_feed.id}")
            create_random_appearance(db_session, faker, event.id, TargetTypeEnum.vuln_feed)
            logger.debug(f"Generating Random Source for Vulnerability Queues {vuln_feed.id}")
            create_random_source(db_session, faker, TargetTypeEnum.vuln_feed, vuln_feed.id)
            logger.debug(f"Generating Random Tag for Vulnerability Queues {vuln_feed.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.vuln_feed, vuln_feed.id)
            logger.debug(f"Generating Random Entity for Vulnerability Queues {vuln_feed.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.vuln_feed, vuln_feed.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.vuln_feed, vuln_feed.id)
            create_random_tag(db_session, faker, TargetTypeEnum.vuln_feed, vuln_feed.id)
            logger.debug(f"Generating Random Permission for Vulnerability Queues {vuln_feed.id}")
            create_random_permission(db_session, random.choice(saved_roles), vuln_feed)
            logger.info(f"Vulnerability Queue {vuln_feed.id} Created")

        logger.info("Generating Vulnerability Track")
        for _ in range(5):
            track = create_random_vuln_track(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, track.id, TargetTypeEnum.vuln_track, users)
            create_random_user_links(db_session, faker, track.id, TargetTypeEnum.vuln_track, random.choice(users))
            logger.info(f"Generating Random Entries for Vulnerability Track {track.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.vuln_track, target_id=track.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Vulnerability Track {track.id}")
            create_random_appearance(db_session, faker, event.id, TargetTypeEnum.vuln_track)
            logger.debug(f"Generating Random Source for Vulnerability Track {track.id}")
            create_random_source(db_session, faker, TargetTypeEnum.vuln_track, track.id)
            logger.debug(f"Generating Random Tag for Vulnerability Track {track.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.vuln_track, track.id)
            logger.debug(f"Generating Random Entity for Vulnerability Track {track.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.vuln_track, track.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.vuln_track, track.id)
            create_random_tag(db_session, faker, TargetTypeEnum.vuln_track, track.id)
            logger.debug(f"Generating Random Permission for Vulnerability Track {track.id}")
            create_random_permission(db_session, random.choice(saved_roles), track)
            logger.info(f"Vulnerability Track {track.id} Created")

        logger.info("Generating Guides")
        for _ in range(5):
            signature = random.choice(signatures)
            guide = create_random_guide(db_session, faker, random.choice(users), signature)
            create_popularity(db_session, faker, guide.id, TargetTypeEnum.guide, users)
            create_random_user_links(db_session, faker, guide.id, TargetTypeEnum.guide, random.choice(users))
            logger.info(f"Generating Random Entries for Signature {signature.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.signature, target_id=signature.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Guide {guide.id}")
            create_random_appearance(db_session, faker, guide.id, TargetTypeEnum.guide)
            logger.debug(f"Generating Random Source for Guide {guide.id}")
            create_random_source(db_session, faker, TargetTypeEnum.guide, guide.id)
            logger.debug(f"Generating Random Tag for Guide {guide.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.guide, guide.id)
            logger.debug(f"Generating Random Permission for Guide {guide.id}")
            create_random_permission(db_session, random.choice(saved_roles), guide)
            logger.debug(f"Generating Link for Guide {guide.id} with Signature {signature.id}")
            create_link(db_session, faker, TargetTypeEnum.signature, signature.id, TargetTypeEnum.guide, guide.id)
            logger.debug(f"Generating Random Entity for Guide {guide.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.guide, guide.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.info(f"Guide {guide.id} Created")

        logger.info("Generating Incidents")
        for _ in range(5):
            incident = create_random_incident(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, incident.id, TargetTypeEnum.incident, users)
            create_random_user_links(db_session, faker, incident.id, TargetTypeEnum.incident, random.choice(users))
            logger.info(f"Generating Random Entries for Incident {incident.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.incident, target_id=incident.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Incident {incident.id}")
            create_random_appearance(db_session, faker, incident.id, TargetTypeEnum.incident)
            logger.debug(f"Generating Random Source for Incident {incident.id}")
            create_random_source(db_session, faker, TargetTypeEnum.incident, incident.id)
            logger.debug(f"Generating Random Tag for Incident {incident.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.incident, incident.id)
            logger.debug(f"Generating Random Entity for Incident {incident.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.incident, incident.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Incident {incident.id}")
            create_random_permission(db_session, random.choice(saved_roles), incident)
            logger.info(f"Incident {incident.id} Created")

        logger.info("Generating Dispatches")
        for _ in range(5):
            dispatch = create_random_dispatch(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, dispatch.id, TargetTypeEnum.dispatch, users)
            create_random_user_links(db_session, faker, dispatch.id, TargetTypeEnum.dispatch, random.choice(users))

            if faker.pybool():
                logger.debug(f"Promoting Dispatches {dispatch.id}")
                promote_dispatch_to_intel(db_session, [dispatch.id])

                if faker.pybool():
                    logger.debug(f"Promoting Dispatches TWICE {dispatch.id}")
                    promote_dispatch_to_intel(db_session, [dispatch.id])

            logger.info(f"Generating Random Entries for Dispatch {dispatch.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.dispatch, target_id=dispatch.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Dispatch {dispatch.id}")
            create_random_appearance(db_session, faker, dispatch.id, TargetTypeEnum.dispatch)
            logger.debug(f"Generating Random Source for Dispatch {dispatch.id}")
            create_random_source(db_session, faker, TargetTypeEnum.dispatch, dispatch.id)
            logger.debug(f"Generating Random Tag for Dispatch {dispatch.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.dispatch, dispatch.id)
            logger.debug(f"Generating Random Entity for Dispatch {dispatch.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.dispatch, dispatch.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Dispatch {dispatch.id}")
            create_random_permission(db_session, random.choice(saved_roles), dispatch)
            logger.info(f"Dispatch {dispatch.id} Created")

        logger.info("Generating Intels")
        for _ in range(5):
            intel = create_random_intel(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, intel.id, TargetTypeEnum.intel, users)
            create_random_user_links(db_session, faker, intel.id, TargetTypeEnum.intel, random.choice(users))
            logger.info(f"Generating Random Entries for Intel {intel.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.intel, target_id=intel.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Intel {intel.id}")
            create_random_appearance(db_session, faker, intel.id, TargetTypeEnum.intel)
            logger.debug(f"Generating Random Source for Intel {intel.id}")
            create_random_source(db_session, faker, TargetTypeEnum.intel, intel.id)
            logger.debug(f"Generating Random Tag for Intel {intel.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.intel, intel.id)
            logger.debug(f"Generating Random Entity for Intel {intel.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.intel, intel.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Intel {intel.id}")
            create_random_permission(db_session, random.choice(saved_roles), intel)
            logger.info(f"Intel {intel.id} Created")

        logger.info("Generating Products")
        for _ in range(5):
            product = create_random_product(db_session, faker, random.choice(users))
            create_random_user_links(db_session, faker, product.id, TargetTypeEnum.product, random.choice(users))
            create_popularity(db_session, faker, product.id, TargetTypeEnum.product, users)
            logger.info(f"Generating Random Entries for Product {product.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.product, target_id=product.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Product {product.id}")
            create_random_appearance(db_session, faker, product.id, TargetTypeEnum.product)
            logger.debug(f"Generating Random Source for Product {product.id}")
            create_random_source(db_session, faker, TargetTypeEnum.product, product.id)
            logger.debug(f"Generating Random Tag for Product {product.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.product, product.id)
            logger.debug(f"Generating Random Entity for Product {product.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.product, product.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Product {product.id}")
            create_random_permission(db_session, random.choice(saved_roles), product)
            logger.info(f"Product {product.id} Created")

        logger.info("Generating Checklists")
        for _ in range(5):
            checklist = create_random_checklist(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, checklist.id, TargetTypeEnum.checklist, users)
            create_random_user_links(db_session, faker, checklist.id, TargetTypeEnum.checklist, random.choice(users))
            logger.info(f"Generating Random Entries for Checklist {checklist.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.checklist, target_id=checklist.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Checklist {checklist.id}")
            create_random_appearance(db_session, faker, checklist.id, TargetTypeEnum.checklist)
            logger.debug(f"Generating Random Source for Checklist {checklist.id}")
            create_random_source(db_session, faker, TargetTypeEnum.checklist, checklist.id)
            logger.debug(f"Generating Random Tag for Checklist {checklist.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.checklist, checklist.id)
            logger.debug(f"Generating Random Entity for Checklist {checklist.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.checklist, checklist.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Checklist {checklist.id}")
            create_random_permission(db_session, random.choice(saved_roles), checklist)
            logger.info(f"Checklist {checklist.id} Created")

        logger.info("Generating Feeds")
        for _ in range(5):
            feed = create_random_feed(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, feed.id, TargetTypeEnum.feed, users)
            create_random_user_links(db_session, faker, feed.id, TargetTypeEnum.feed, random.choice(users))
            logger.info(f"Generating Random Entries for Feed {feed.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.feed, target_id=feed.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Feed {feed.id}")
            create_random_appearance(db_session, faker, feed.id, TargetTypeEnum.feed)
            logger.debug(f"Generating Random Source for Feed {feed.id}")
            create_random_source(db_session, faker, TargetTypeEnum.feed, feed.id)
            logger.debug(f"Generating Random Tag for Feed {feed.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.feed, feed.id)
            logger.debug(f"Generating Random Entity for Feed {feed.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.feed, feed.id)
            create_popularity(db_session, faker, entity.id, TargetTypeEnum.entity, users)
            create_random_user_links(db_session, faker, entity.id, TargetTypeEnum.entity, random.choice(users))
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Feed {feed.id}")
            create_random_permission(db_session, random.choice(saved_roles), feed)
            logger.info(f"Feed {feed.id} Created")

        logger.info("Generating Files")
        for _ in range(5):
            file = create_random_file(db_session, faker, random.choice(users))
            create_popularity(db_session, faker, file.id, TargetTypeEnum.file, users)
            logger.info(f"Generating Random Entries for File {file.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.file, target_id=file.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for File {file.id}")
            create_random_appearance(db_session, faker, file.id, TargetTypeEnum.file)
            logger.debug(f"Generating Random Source for File {file.id}")
            create_random_source(db_session, faker, TargetTypeEnum.file, file.id)
            logger.debug(f"Generating Random Tag for File {file.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.file, file.id)
            logger.debug(f"Generating Random Entity for File {file.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.file, file.id)
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for File {file.id}")
            create_random_permission(db_session, random.choice(saved_roles), file)
            logger.info(f"File {file.id} Created")

        logger.info("Generating Notifications")
        for _ in range(5):
            notification = create_random_notification(db_session, faker, random.choice(users).id)
            logger.info(f"Notification {notification.id} Created")

        logger.info("Generating Games")
        for _ in range(5):
            signature = random.choice(signatures)
            _user = crud.user.get_by_username(db_session, username=signature.owner)
            audit = create_audit(db_session, faker, _user, signature)
            game = create_random_game(db_session, faker, audit)
            logger.info(f"Game {game.id} Created")

        logger.info("Generating Threat Model Item")
        for _ in range(5):
            threat_model_item = create_random_threat_model_item(db_session, faker)
            create_popularity(db_session, faker, threat_model_item.id, TargetTypeEnum.threat_model_item, users)
            logger.info(f"Generating Random Entries for Threat Model Item {threat_model_item.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.threat_model_item, target_id=threat_model_item.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Threat Model Item {threat_model_item.id}")
            create_random_appearance(db_session, faker, threat_model_item.id, TargetTypeEnum.threat_model_item)
            logger.debug(f"Generating Random Source for Threat Model Item {threat_model_item.id}")
            create_random_source(db_session, faker, TargetTypeEnum.threat_model_item, threat_model_item.id)
            logger.debug(f"Generating Random Tag for Threat Model Item {threat_model_item.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.threat_model_item, threat_model_item.id)
            logger.debug(f"Generating Random Entity for Threat Model Item {threat_model_item.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.threat_model_item, threat_model_item.id)
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Threat Model Item {threat_model_item.id}")
            create_random_permission(db_session, random.choice(saved_roles), threat_model_item)
            logger.info(f"Threat Model Item {threat_model_item.id} Created")

        logger.info("Generating Stat")
        for _ in range(5):
            stat = create_random_stat(db_session, faker)
            create_popularity(db_session, faker, stat.id, TargetTypeEnum.stat, users)
            logger.info(f"Generating Random Entries for Stat {stat.id}")
            entry = create_random_entry(db_session, faker, target_type=TargetTypeEnum.stat, target_id=stat.id)
            create_popularity(db_session, faker, entry.id, TargetTypeEnum.entry, users)
            create_random_user_links(db_session, faker, entry.id, TargetTypeEnum.entry, random.choice(users))
            logger.debug(f"Generating Random Appearance for Stat {stat.id}")
            create_random_appearance(db_session, faker, stat.id, TargetTypeEnum.stat)
            logger.debug(f"Generating Random Source for Stat {stat.id}")
            create_random_source(db_session, faker, TargetTypeEnum.stat, stat.id)
            logger.debug(f"Generating Random Tag for Stat {stat.id}")
            create_random_tag(db_session, faker, TargetTypeEnum.stat, stat.id)
            logger.debug(f"Generating Random Entity for Stat {stat.id}")
            entity = create_random_entity(db_session, faker, TargetTypeEnum.stat, stat.id)
            # create source and tag for entity
            create_random_source(db_session, faker, TargetTypeEnum.entity, entity.id)
            create_random_tag(db_session, faker, TargetTypeEnum.entity, entity.id)
            logger.debug(f"Generating Random Permission for Stat {stat.id}")
            create_random_permission(db_session, random.choice(saved_roles), stat)
            logger.info(f"Threat Model Item {stat.id} Created")

        logger.info("Generating Remote Flair")
        for _ in range(5):
            create_random_remote_flair(db_session, faker)

        db_session.commit()
        logger.info("Finished Generating Data")

        try:
            index_search_results()
        except Exception:
            pass

        logger.info("Initial data created")

    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    main()
