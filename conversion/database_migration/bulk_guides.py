import tqdm
import json
import os
from datetime import datetime
from datetime import timezone
import csv
from conversion_utilities import write_permission, write_tag_source_links

def main(mongo_db=None, role_lookup=None, tag_lookup=None, source_lookup=None):
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    scot3_guide_count = mongo_db.guide.count_documents({})
    scot3_guides = mongo_db.guide.find()
    permission_csv = open(f'{staging_directory}/guide_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])
    with open(f'{staging_directory}/guides.csv','w+') as guide_csv:
        writer = csv.writer(guide_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['guide_id', 'owner', 'tlp', 'subject', 'created_date', 'modified_date', 'guide_data'])
        with tqdm.tqdm(total=scot3_guide_count) as pbar:
            for guide in scot3_guides:
                tlp = guide.get('tlp')
                if tlp is None:
                    tlp = 'unset'
                elif tlp == 'amber+strict':
                    tlp = 'amber_strict'
                if guide.get('subject') is not None:
                    new_guide = [guide['id'], 'scot-admin', tlp, guide['subject'], datetime.fromtimestamp(guide['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(guide['updated']).astimezone(timezone.utc).replace(tzinfo=None), json.dumps(guide.get('data')) ]
                else:
                    new_guide = [ guide['id'], 'scot-admin', tlp, "NO SUBJECT", datetime.fromtimestamp(guide['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(guide['updated']).astimezone(timezone.utc).replace(tzinfo=None), json.dumps(guide.get('data'))]
                writer.writerow(new_guide)
                write_permission(thing=guide, thing_type='guide', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                pbar.update(1)
if __name__ == "__main__":
    main()
