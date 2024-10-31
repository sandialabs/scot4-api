import json
import csv
import os
import tqdm
from datetime import datetime
from datetime import timezone
from conversion_utilities import write_permission, write_tag_source_links

def main(mongo_db=None, role_lookup=None, tag_lookup=None, source_lookup=None):
    scot3_incident_count = mongo_db.incident.count_documents({})
    scot3_incidents = mongo_db.incident.find()
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    permission_csv = open(f'{staging_directory}/incident_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])

    links_csv = open(f'{staging_directory}/incident_links.csv','w+')
    link_csv_writer = csv.writer(links_csv, dialect='unix', delimiter='\t', quotechar="'")
    link_csv_writer.writerow(['v0_type', 'v0_id', 'v1_type', 'v1_id'])
    with open(f'{staging_directory}/incidents.csv','w+') as incident_csv:
        writer = csv.writer(incident_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['incident_id', 'tlp', 'owner', 'status', 'subject', 'created_date', 'modified_date', 'incident_data', 'incident_data_ver', 'reported_date', 'discovered_date', 'occurred_date'])
        with tqdm.tqdm(total=scot3_incident_count) as pbar:
            for incident in scot3_incidents:
                reported = incident['data'].get('reported')
                discovered = incident['data'].get('discovered')
                occurred = incident['data'].get('occurred')
                tlp = incident.get('tlp')
                version = incident.get('data_fmt_ver')
                if tlp is None:
                    tlp = 'unset'
                elif tlp =='amber+strict':
                    tlp = 'amber_strict'
                inc_ts = {}
                if reported is not None:
                    reported_date = datetime.fromtimestamp(reported).astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    reported_date = None
                if discovered is not None:
                    discovered_date  = datetime.fromtimestamp(discovered).astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    discovered_date = None
                if occurred is not None:
                    occurred_date = datetime.fromtimestamp(occurred).astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    occurred_date = None
                new_incident = [incident['id'], tlp, incident['owner'], incident['status'],  incident['subject'], datetime.fromtimestamp(incident['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(incident['updated']).astimezone(timezone.utc).replace(tzinfo=None), json.dumps(incident['data']), version, reported_date, discovered_date, occurred_date]
                writer.writerow(new_incident)
                write_permission(thing=incident, thing_type='incident', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                write_tag_source_links(thing=incident, thing_type='incident', tag_lookup=tag_lookup, source_lookup=source_lookup, link_csv_writer=link_csv_writer)               
                pbar.update(1)
    permission_csv.close()
    links_csv.close()
if __name__ == "__main__":
    main()
