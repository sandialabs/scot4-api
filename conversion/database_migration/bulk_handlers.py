import os
import json
import traceback
from datetime import datetime
from datetime import timezone
import tqdm
import csv

def main(mongo_db=None):
    scot3_handler_count = mongo_db.handler.count_documents({})
    scot3_handlers = mongo_db.handler.find()
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    with open(f'{staging_directory}/handlers.csv','w+') as handler_csv:
        writer = csv.writer(handler_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['handler_id', 'start_date', 'end_date', 'username', 'position', 'created_date', 'modified_date'])
        with tqdm.tqdm(total=scot3_handler_count) as pbar:
            bulk_array = []
            for handler in scot3_handlers:
                if type(handler.get('start')) is not int or type(handler.get('end')) is not int:
                    pbar.update(1)
                    continue
                if handler['type'] == 'handler':
                    handler['type'] = 'incident handler'
                new_handler = [handler['id'], datetime.fromtimestamp(handler['start']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(handler['end']).astimezone(timezone.utc).replace(tzinfo=None), handler['username'], handler['type'], datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None)]
                writer.writerow(new_handler)
                pbar.update(1)
