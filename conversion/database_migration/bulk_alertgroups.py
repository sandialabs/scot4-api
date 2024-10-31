import csv
import os
from datetime import datetime
from datetime import timezone
import tqdm
from conversion_utilities import write_permission, write_tag_source_links

def main(mongo_db=None, role_lookup=None, tag_lookup=None, source_lookup=None):
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    permission_csv = open(f'{staging_directory}/alertgroup_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])

    links_csv = open(f'{staging_directory}/alertgroup_links.csv','w+')
    link_csv_writer = csv.writer(links_csv, dialect='unix', delimiter='\t', quotechar="'")
    link_csv_writer.writerow(['v0_type', 'v0_id', 'v1_type', 'v1_id'])
    scot3_alertgroup_count = mongo_db.alertgroup.count_documents({})
    scot3_alertgroups = mongo_db.alertgroup.find()
    with open(f'{staging_directory}/alertgroups.csv', 'w+') as alertgroup_schema_keys_csv:
        writer = csv.writer(alertgroup_schema_keys_csv, dialect='unix', delimiter="\t", quotechar="'")
        writer.writerow(['alertgroup_id', 'tlp', 'subject', 'created_date', 'modified_date', 'view_count'])
        with tqdm.tqdm(total=scot3_alertgroup_count) as pbar:
            for alertgroup in scot3_alertgroups:
                view_count = alertgroup.get('views')
                if view_count is None:
                    view_count = 0
                new_alertgroup = [alertgroup['id'], 'unset', alertgroup['subject'], datetime.fromtimestamp(alertgroup['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(alertgroup['updated']).astimezone(timezone.utc).replace(tzinfo=None), view_count]
                writer.writerow(new_alertgroup)
                write_permission(thing=alertgroup, thing_type='alertgroup', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                write_tag_source_links(thing=alertgroup, thing_type='alertgroup', tag_lookup=tag_lookup, source_lookup=source_lookup, link_csv_writer=link_csv_writer)
                pbar.update(1)

    permission_csv.close()
    links_csv.close() 
if __name__ == "__main__":
    main()
