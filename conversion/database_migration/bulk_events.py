from datetime import datetime
from datetime import timezone
import csv
import os
import tqdm
from conversion_utilities import write_tag_source_links, write_permission

def main(mongo_db=None, role_lookup=None, tag_lookup=None, source_lookup=None):
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    permission_csv = open(f'{staging_directory}/event_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])

    links_csv = open(f'{staging_directory}/event_links.csv','w+')
    link_csv_writer = csv.writer(links_csv, dialect='unix', delimiter='\t', quotechar="'")
    link_csv_writer.writerow(['v0_type', 'v0_id', 'v1_type', 'v1_id'])
    scot3_event_count = mongo_db.event.count_documents({})
    scot3_events = mongo_db.event.find()
    with open(f'{staging_directory}/events.csv','w+') as events_csv:
        writer = csv.writer(events_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['event_id', 'owner', 'status', 'subject', 'created_date', 'modified_date', 'tlp', 'view_count'])
        with tqdm.tqdm(total=scot3_event_count) as pbar:
            for event in scot3_events:
                tlp = event.get('tlp')
                if tlp is None:
                    tlp = 'unset'
                elif tlp == 'amber+strict':
                    tlp = 'amber_strict'
                new_event = [event['id'], event['owner'], event['status'], event['subject'], datetime.fromtimestamp(event['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(event['updated']).astimezone(timezone.utc).replace(tzinfo=None), tlp, event['views']]
                writer.writerow(new_event)
                write_permission(thing=event, thing_type='event', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                write_tag_source_links(thing=event, thing_type='event', tag_lookup=tag_lookup, source_lookup=source_lookup, link_csv_writer=link_csv_writer)               
                pbar.update(1)
    permission_csv.close()
    links_csv.close()
