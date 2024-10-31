import traceback
import os
import pymongo
import csv
import bulk_roles
import bulk_handlers
import bulk_signatures
import bulk_tags
import bulk_sources
import bulk_alert_data
import bulk_guides
import bulk_alerts
import bulk_alertgroups
import bulk_events
import bulk_incidents
import bulk_dispatches
import bulk_intels
import bulk_products
import bulk_promotions
import bulk_entities_and_entity_types
import bulk_enrichments
import bulk_entity_class_associations
import bulk_entries
import bulk_links
import multiprocessing as mp


if __name__=="__main__":
    if os.getenv('MONGO_DB_URI') is None or os.getenv('MONGO_DB_NAME') is None or os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY') is None:
        print('Please set the following environment variables:\nMONGO_DB_URI\nMONGO_DB_NAME\nSCOT_MIGRATION_STAGING_DIRECTORY')
        exit(1)

    mongo_session = pymongo.MongoClient(os.getenv('MONGO_DB_URI'))[os.getenv('MONGO_DB_NAME')]
    try:
        staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')


        ## Get ID to Thing Lookups for roles, sources, and tags and export these to CSV's 
        role_lookup = bulk_roles.main(mongo_db=mongo_session)
        source_lookup = bulk_sources.main(mongo_db=mongo_session)
        tag_lookup = bulk_tags.main(mongo_db=mongo_session)
        next_entry_id = bulk_entries.main(mongo_db=mongo_session, role_lookup=role_lookup)

        ## IR Elements
        bulk_alert_data_process = mp.Process(target=bulk_alert_data.main, kwargs={'mongo_db': mongo_session})
        bulk_handlers_process = mp.Process(target=bulk_handlers.main, kwargs={'mongo_db': mongo_session})
        bulk_alerts_process = mp.Process(target=bulk_alerts.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup})
        bulk_alertgroups_process = mp.Process(target=bulk_alertgroups.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup, 'source_lookup': source_lookup, 'tag_lookup': tag_lookup})
        bulk_events_process = mp.Process(target=bulk_events.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup, 'source_lookup': source_lookup, 'tag_lookup': tag_lookup})
        bulk_incidents_process = mp.Process(target=bulk_incidents.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup, 'source_lookup': source_lookup, 'tag_lookup': tag_lookup})
        bulk_guides_process = mp.Process(target=bulk_guides.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup, 'source_lookup': source_lookup, 'tag_lookup': tag_lookup})

        bulk_dispatches_process = mp.Process(target=bulk_dispatches.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup, 'source_lookup': source_lookup, 'tag_lookup': tag_lookup})
        bulk_intels_process = mp.Process(target=bulk_intels.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup, 'source_lookup': source_lookup, 'tag_lookup': tag_lookup})
        bulk_products_process = mp.Process(target=bulk_products.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup, 'source_lookup': source_lookup, 'tag_lookup': tag_lookup})
        bulk_signatures_process = mp.Process(target=bulk_signatures.main, kwargs={'mongo_db': mongo_session, 'role_lookup': role_lookup, 'source_lookup': source_lookup, 'tag_lookup': tag_lookup})
        bulk_promotions_process = mp.Process(target=bulk_promotions.main, kwargs={'mongo_db': mongo_session, 'role_lookup':role_lookup, 'entry_id': next_entry_id})

        bulk_entities_and_entity_types_process = mp.Process(target=bulk_entities_and_entity_types.main, kwargs={'mongo_db': mongo_session})
        bulk_enrichments_process = mp.Process(target=bulk_enrichments.main, kwargs={'mongo_db': mongo_session})
        bulk_entity_class_associations_process = mp.Process(target=bulk_entity_class_associations.main, kwargs={'mongo_db': mongo_session})

        bulk_links_process = mp.Process(target=bulk_links.main, kwargs={'mongo_db': mongo_session})

        bulk_alert_data_process.start()
        bulk_alerts_process.start()
        bulk_alertgroups_process.start()
        bulk_events_process.start()
        bulk_incidents_process.start()
        bulk_handlers_process.start()
        bulk_signatures_process.start()

        bulk_dispatches_process.start()
        bulk_intels_process.start()
        bulk_products_process.start()


        bulk_promotions_process.start()
        bulk_entities_and_entity_types_process.start()
        bulk_enrichments_process.start()
        bulk_entity_class_associations_process.start()
        bulk_links_process.start()
        bulk_guides_process.start()

        bulk_alert_data_process.join()
        bulk_alerts_process.join()
        bulk_alertgroups_process.join()
        bulk_events_process.join()
        bulk_incidents_process.join()
        bulk_signatures_process.join()

        bulk_handlers_process.join()
        bulk_dispatches_process.join()
        bulk_intels_process.join()
        bulk_products_process.join()


        bulk_promotions_process.join()
        bulk_entities_and_entity_types_process.join()
        bulk_enrichments_process.join()
        bulk_entity_class_associations_process.join()
        bulk_links_process.join()
        bulk_guides_process.join()
        
    except Exception:
        print(f"Error: {traceback.format_exc()}")
