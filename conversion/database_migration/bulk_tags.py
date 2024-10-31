import os
import csv
import tqdm
from datetime import datetime
from datetime import timezone

def main(mongo_db=None):
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    tag_lookup = {}
    with open(f'{staging_directory}/tags.csv','w+') as tag_csv:
        writer = csv.writer(tag_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['tag_id', 'tag_name', 'description', 'created_date', 'modified_date'])
        scot3_tags = mongo_db.tag.distinct('value')
        for count, tag in enumerate(tqdm.tqdm(scot3_tags)):
            if tag.lower()[:250] not in tag_lookup:
                new_tag = [count+1, tag.lower()[:250], "Migrated from SCOT3", datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None)]
                writer.writerow(new_tag)
                tag_lookup[tag.lower()[:250]] = count+1
    return tag_lookup
