import pymongo
from datetime import datetime
from datetime import timezone
import csv
import os
import tqdm
import json
from conversion_utilities import write_tag_source_links, write_permission

def main(mongo_db=None, role_lookup=None, tag_lookup=None, source_lookup=None):
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    permission_csv = open(f'{staging_directory}/signature_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])

    links_csv = open(f'{staging_directory}/signature_links.csv','w+')
    link_csv_writer = csv.writer(links_csv, dialect='unix', delimiter='\t', quotechar="'")
    link_csv_writer.writerow(['v0_type', 'v0_id', 'v1_type', 'v1_id'])
    scot3_signature_count = mongo_db.signature.count_documents({})
    scot3_signatures = mongo_db.signature.find()
        
    with open(f'{staging_directory}/signatures.csv','w+') as signatures_csv:
        writer = csv.writer(signatures_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['signature_id', 'owner', 'status', 'name', 'created_date', 'modified_date', 'tlp', 'signature_data', 'latest_revision', 'signature_type','signature_description'])
        with tqdm.tqdm(total=scot3_signature_count) as pbar:
            for signature in scot3_signatures:
                sig_bodies = mongo_db.sigbody.find({'signature_id': signature['id']})
                sorted_sig_bodies = sorted([sig_body for sig_body in sig_bodies], key=lambda x: x['revision'], reverse=True)
                if len(sorted_sig_bodies) == 0:
                    continue
                else:
                    latest_sig_body = sorted_sig_bodies[0]
                tlp = signature.get('tlp')
                description = signature['data'].get('description')
                if tlp is None:
                    tlp = 'unset'
                elif tlp == 'amber+strict':
                    tlp = 'amber_strict'
                sig_type = signature.get('data').get('type')
                if sig_type is None:
                    sig_type = "unknown"
                sig_data = {'signature_body': latest_sig_body['body'], 'signature_bodyb64': latest_sig_body['bodyb64']}
                sig_data.update(signature['data'])
                new_signature = [signature['id'], signature['owner'], signature['status'], signature['name'], datetime.fromtimestamp(signature['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(signature['updated']).astimezone(timezone.utc).replace(tzinfo=None), tlp, json.dumps(sig_data), 1, sig_type, description]
                writer.writerow(new_signature)
                write_permission(thing=signature, thing_type='signature', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                write_tag_source_links(thing=signature, thing_type='signature', tag_lookup=tag_lookup, source_lookup=source_lookup, link_csv_writer=link_csv_writer)               
                pbar.update(1)
    permission_csv.close()
    links_csv.close()

if __name__ == "__main__":
    mongo_session = pymongo.MongoClient(os.getenv('MONGO_DB_URI'))[os.getenv('MONGO_DB_NAME')]
    main(mongo_db=mongo_session)
