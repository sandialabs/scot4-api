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
    scot3_entities_count = mongo_db.entity.count_documents({})
    scot3_entities = mongo_db.entity.find()

    with tqdm.tqdm(total=scot3_entities_count) as pbar:
        with open(f"{staging_directory}/enrichments.csv",'w+') as enrichments_csv:
            writer = csv.writer(enrichments_csv, dialect='unix', delimiter='\t', quotechar="'")
            writer.writerow(['created_date', 'modified_date', 'entity_id', 'enrichment_title', 'enrichment_class', 'enrichment_data'])
            for entity in scot3_entities:
                if len(entity['value']) > 65000:
                    pbar.update(1)
                    continue
                # Want to skip this entity if it has no data
                if entity.get('data') is None:
                    pbar.update(1)
                    continue

                # Get created_date from mongo ObjectID
                created_date = entity['_id'].generation_time.astimezone(timezone.utc).replace(tzinfo=None)

                # Possibly getting many enrichments per entity 
                enrichments = []

                # binip
                if entity['data'].get('binip') is not None:
                    binip_enrichment = [created_date, created_date, entity['id'], 'binip', 'plaintext', json.dumps({"plaintext": entity['data']['binip']})]
                    enrichments.append(binip_enrichment)

                # geoip
                if entity['data'].get('geoip') is not None:
                    geoip_enrichment = [created_date, created_date, entity['id'], 'geoip', 'jsontree', json.dumps(entity['data']['geoip'].get('data'))]
                    enrichments.append(geoip_enrichment)

                # blocklist
                if entity['data'].get('blocklist3') is not None:
                    blocklist_enrichment = [created_date, created_date, entity['id'], 'blocklist3', 'jsontree', json.dumps(entity['data']['blocklist3'].get('data'))]
                    enrichments.append(blocklist_enrichment)

                # lri
                if entity['data'].get('lri') is not None:
                    lri_enrichment = [created_date, created_date, entity['id'], 'lri', 'jsontree', json.dumps(entity['data']['lri'].get('data'))]
                    enrichments.append(lri_enrichment)
                
                for new_enrichment in enrichments:
                    writer.writerow(new_enrichment)
                
                pbar.update(1)


