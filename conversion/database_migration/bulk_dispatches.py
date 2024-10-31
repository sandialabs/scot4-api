import csv
import os
import tqdm
from datetime import datetime
from datetime import timezone
from conversion_utilities import write_permission, write_tag_source_links

def main(mongo_db=None, role_lookup=None, tag_lookup=None, source_lookup=None):
    scot3_dispatch_count = mongo_db.dispatch.count_documents({})
    scot3_dispatchs = mongo_db.dispatch.find()
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    permission_csv = open(f'{staging_directory}/dispatch_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])

    links_csv = open(f'{staging_directory}/dispatch_links.csv','w+')
    link_csv_writer = csv.writer(links_csv, dialect='unix', delimiter='\t', quotechar="'")
    link_csv_writer.writerow(['v0_type', 'v0_id', 'v1_type', 'v1_id'])
    with open(f'{staging_directory}/dispatch.csv','w+') as dispatch_csv:
        writer = csv.writer(dispatch_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['dispatch_id', 'tlp', 'owner', 'status', 'subject', 'created_date', 'modified_date'])
        with tqdm.tqdm(total=scot3_dispatch_count) as pbar:
            for dispatch in scot3_dispatchs:
                tlp = dispatch.get('tlp')
                if tlp is None:
                    tlp = 'unset'
                elif tlp == 'amber+strict':
                    tlp = 'amber_strict'
                new_dispatch = [dispatch['id'], tlp, dispatch['owner'], dispatch['status'], dispatch['subject'], datetime.fromtimestamp(dispatch['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(dispatch['updated']).astimezone(timezone.utc).replace(tzinfo=None)]
                writer.writerow(new_dispatch)
                write_permission(thing=dispatch, thing_type='dispatch', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                write_tag_source_links(thing=dispatch, thing_type='dispatch', tag_lookup=tag_lookup, source_lookup=source_lookup, link_csv_writer=link_csv_writer)
                pbar.update(1)
    permission_csv.close()
    links_csv.close()

if __name__ == "__main__":
    main()
