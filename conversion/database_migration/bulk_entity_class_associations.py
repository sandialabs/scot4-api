import os
import csv
import json
import tqdm
import bson
from datetime import datetime
from datetime import timezone

def get_flag_ecid(geoip_data, ec_lookup):
    try:
        if geoip_data.get('isocode') is None:
            return None

        flag_string = f"{geoip_data['isocode'].lower()}_flag"
        if ec_lookup.get(flag_string) is not None:
            return ec_lookup.get(flag_string)
        else:
            return None
    except:
        print("ERROR: Exception in get_flag_ecid()")
        print(f"ERROR: geoip_data was: {geoip_data}")
        return None

def main(mongo_db=None):
    entity_type_lookup = {}
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    scot3_entities_count = mongo_db.entity.count_documents({})
    scot3_entities = mongo_db.entity.find()
    ec_lookup = {}

    # Load entity_class_ids from csv
    with open("./entity_classes.csv", 'r') as ec_csv:
        entity_classes = csv.reader(ec_csv, delimiter='\t')

        # skip header
        next(entity_classes)

        for entity_class in entity_classes: 
            ec_lookup[entity_class[1]] = entity_class[0]

    # Loop through all entities to get associations
    with tqdm.tqdm(total=scot3_entities_count) as pbar:
        with open(f"{staging_directory}/entity_class_associations.csv",'w+') as entity_class_associations_csv:
            writer = csv.writer(entity_class_associations_csv, dialect='unix', delimiter='\t', quotechar="'")
            writer.writerow(['entity_id', 'entity_class_id'])
            for entity in scot3_entities:
                if len(entity['value']) > 65000:
                    pbar.update(1)
                    continue
                # Want to skip this entity if it has no data
                if entity.get('data') is None:
                    pbar.update(1)
                    continue

                # Possibly getting many associations per entity 
                associations = []

                # from geoip data
                if entity['data'].get('geoip') is not None and entity['data']['geoip'].get('data') is not None:
                   
                    # Make sure the data wasn't errored
                    if entity['data']['geoip'].get('type') == "error":
                        pbar.update(1)
                        continue

                    # Make sure the data isn't malformed
                    if type(entity['data']['geoip']['data']) is not dict:
                        print(f"WARN: Could not load geoip data for entity {entity['id']}. Data was: {entity}")
                        pbar.update(1)
                        continue
                            
                    # flag data
                    if (ecid := get_flag_ecid(entity['data']['geoip']['data'], ec_lookup)) is not None:
                        associations.append([entity['id'], ecid])

                    # Sandia 
                    if entity['data']['geoip']['data'].get('org') == "Sandia National Laboratories":
                        associations.append([entity['id'], 251])

                    # Anonymous IP
                    if entity['data']['geoip']['data'].get('is_anonymous') == 1:
                        associations.append([entity['id'], 253])

                    # Anonymous VPN
                    if entity['data']['geoip']['data'].get('is_anonymous_vpn') == 1:
                        associations.append([entity['id'], 254])

                    # Hosting Provider
                    if entity['data']['geoip']['data'].get('is_hosting_provider') == 1:
                        associations.append([entity['id'], 255])

                    # Public Proxy
                    if entity['data']['geoip']['data'].get('is_public_proxy') == 1:
                        associations.append([entity['id'], 256])

                    # Tor Exit Node
                    if entity['data']['geoip']['data'].get('is_tor_exit_node') == 1:
                        associations.append([entity['id'], 257])

                # from blocklist
                if entity['data'].get('blocklist3') is not None and entity['data']['blocklist3'].get('data') is not None:
                    
                    # Firewall block
                    if entity['data']['blocklist3']['data'].get('firewall') == 1:
                        associations.append([entity['id'], 252])

                    # Blackhole
                    if entity['data']['blocklist3']['data'].get('blackhole') == 1:
                        associations.append([entity['id'], 258])

                    # Proxy block
                    if entity['data']['blocklist3']['data'].get('proxy_block') == 1:
                        associations.append([entity['id'], 259])

                    # Watchlist
                    if entity['data']['blocklist3']['data'].get('watch') == 1:
                        associations.append([entity['id'], 260])

                    # Whitelist
                    if entity['data']['blocklist3']['data'].get('whitelist') == 1:
                        associations.append([entity['id'], 261])

                # from scanner
                if entity['data'].get('scanner') is not None and entity['data']['scanner'].get('active') == "true":
                    associations.append([entity['id'], 250])
                
                for new_association in associations:
                    writer.writerow(new_association)
                
                pbar.update(1)
