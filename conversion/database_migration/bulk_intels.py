import csv
import os
import tqdm
from datetime import datetime
from datetime import timezone
from conversion_utilities import write_permission, write_tag_source_links

def main(mongo_db=None, role_lookup=None, tag_lookup=None, source_lookup=None):
    scot3_intel_count = mongo_db.intel.count_documents({})
    scot3_intels = mongo_db.intel.find()
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    permission_csv = open(f'{staging_directory}/intel_permissions.csv','w+')
    permission_csv_writer =csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])

    links_csv = open(f'{staging_directory}/intel_links.csv','w+')
    link_csv_writer =csv.writer(links_csv, dialect='unix', delimiter='\t', quotechar="'")
    link_csv_writer.writerow(['v0_type', 'v0_id', 'v1_type', 'v1_id'])
    with open(f'{staging_directory}/intel.csv','w+') as intels_csv:
        writer = csv.writer(intels_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['intel_id', 'tlp', 'owner', 'status', 'subject', 'created_date', 'modified_date'])
        with tqdm.tqdm(total=scot3_intel_count) as pbar:
            for intel in scot3_intels:
                tlp = intel.get('tlp')
                if tlp is None:
                    tlp = 'unset'
                elif tlp =='amber+strict':
                    tlp = 'amber_strict'
                new_intel = [ intel['id'], tlp, intel['owner'], intel['status'], intel['subject'], datetime.fromtimestamp(intel['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(intel['updated']).astimezone(timezone.utc).replace(tzinfo=None)]
                writer.writerow(new_intel)
                write_permission(thing=intel, thing_type='intel', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                write_tag_source_links(thing=intel, thing_type='intel', tag_lookup=tag_lookup, source_lookup=source_lookup, link_csv_writer=link_csv_writer)               
                pbar.update(1)
    permission_csv.close()
    links_csv.close()
if __name__ == "__main__":
    main()
