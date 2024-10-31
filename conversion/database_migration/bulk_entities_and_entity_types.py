import os
import csv
import json
import tqdm
import bson
from datetime import datetime
from datetime import timezone

def main(mongo_db=None):
    entity_type_lookup = {}
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    with open(f'{staging_directory}/entity_types.csv','w+') as entity_type_csv:
        writer = csv.writer(entity_type_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['entity_type_id', 'entity_type_name', 'created_date', 'modified_date'])
        scot3_entity_types = mongo_db.entity.distinct('type')
        for count, entity_type in enumerate(tqdm.tqdm(scot3_entity_types)):
            new_entity_type = [count+1, entity_type.lower(), datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None)]
            entity_type_lookup[entity_type.lower()] =  count+1
            writer.writerow(new_entity_type)

    scot3_entities_count = mongo_db.entity.count_documents({})
    scot3_entities = mongo_db.entity.find()

    with tqdm.tqdm(total=scot3_entities_count) as pbar:
        with open(f"{staging_directory}/entity_data.csv",'w+') as entity_data_csv:
            writer = csv.writer(entity_data_csv, dialect='unix', delimiter='\t', quotechar="'")
            writer.writerow(['created_date', 'modified_date', 'entity_id', 'status', 'entity_value', 'type_id'])
            for entity in scot3_entities:
                if len(entity['value']) > 65000:
                    continue
                if entity.get('status') is not None:
                    entity_status = entity.get('status')
                else:
                    entity_status = 'untracked'

                # Get created_date from mongo ObjectID
                created_date = entity['_id'].generation_time.astimezone(timezone.utc).replace(tzinfo=None)
                new_entity = [created_date, created_date, entity['id'], entity_status, entity['value'], entity_type_lookup[entity['type']]]
                writer.writerow(new_entity)
                pbar.update(1)


