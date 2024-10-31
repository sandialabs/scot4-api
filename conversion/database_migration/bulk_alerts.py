from datetime import datetime
from datetime import timezone
import os
import tqdm
import csv
from conversion_utilities import write_permission, write_tag_source_links

def main(mongo_db=None, role_lookup=None):
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    permission_csv = open(f'{staging_directory}/alert_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['object_permission_id', 'role_id', 'target_type', 'target_id', 'permission'])
    scot3_alert_count = mongo_db.alert.count_documents({})
    scot3_alerts = mongo_db.alert.find()
    with tqdm.tqdm(total=scot3_alert_count) as pbar:
        with open(f'{staging_directory}/alerts.csv','w+') as alert_meta_data_csv:
            writer = csv.writer(alert_meta_data_csv, dialect='unix', delimiter='\t', quotechar="'")
            writer.writerow(['created_date', 'modified_date', 'alert_id', 'owner', 'tlp', 'status', 'parsed', 'alertgroup_id'])
            for alert in scot3_alerts:
                tlp = alert.get('tlp')
                if tlp is None:
                    tlp = 'unset'
                elif tlp =='amber+strict':
                    tlp = 'amber_strict'
                new_alert = [datetime.fromtimestamp(alert['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(alert['updated']).astimezone(timezone.utc).replace(tzinfo=None), alert['id'], 'scot-admin', tlp, alert['status'], 1, alert['alertgroup']]
                writer.writerow(new_alert)
                write_permission(thing=alert, thing_type='alert', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                pbar.update(1)
