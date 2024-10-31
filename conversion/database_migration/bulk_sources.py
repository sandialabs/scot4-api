import csv
import tqdm
import os
from datetime import datetime
from datetime import timezone

def main(mongo_db=None):
    source_lookup = {}
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    with open(f'{staging_directory}/sources.csv','w+') as source_csv:
        writer = csv.writer(source_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['source_id', 'source_name', 'description', 'created_date', 'modified_date'])
        scot3_sources = mongo_db.source.distinct('value')
        for count, source in enumerate(tqdm.tqdm(scot3_sources)):
            if source.lower()[:250] not in source_lookup:
                new_source = [count+1, source.lower()[:250], "Migrated from SCOT3", datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None)]
                writer.writerow(new_source)
                source_lookup[source.lower()[:250]] = count+1
        
    return source_lookup
