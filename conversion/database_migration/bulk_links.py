import os
import tqdm
import csv
from datetime import datetime
from datetime import timezone


def main(mongo_db=None):
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    links_csv = open(f'{staging_directory}/links.csv','w+')
    link_csv_writer = csv.writer(links_csv, dialect='unix', delimiter='\t', quotechar="'")
    link_csv_writer.writerow(['created_date', 'modified_date', 'link_id', 'v0_type', 'v0_id', 'v1_type', 'v1_id'])
    scot3_link_count = mongo_db.link.count_documents({})
    scot3_links = mongo_db.link.find()
    with tqdm.tqdm(total=scot3_link_count) as pbar:
        for link in scot3_links:
            if link.get('vertices') is None:
                pbar.update(1)
                continue
            if type(link.get('when')) is int:
                new_link = [ datetime.fromtimestamp(link['when']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None), link['id'], link['vertices'][1]['type'], link['vertices'][1]['id'], link['vertices'][0]['type'], link['vertices'][0]['id']]
            else:
                new_link = [datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None), link['id'], link['vertices'][1]['type'], link['vertices'][1]['id'], link['vertices'][0]['type'], link['vertices'][0]['id']]
            link_csv_writer.writerow(new_link)
            pbar.update(1)
    links_csv.close()

if __name__ == "__main__":
    main()
