import tqdm
import os
import json
import re
import csv
from datetime import datetime
from datetime import timezone

def write_promotion_entry_permissions(mongo_db=None, promotion_entries=None, role_lookup=None, permission_csv_writer=None):
    for promotion_entry in promotion_entries:
        target_id = promotion_entry['target_id']
        target_type = promotion_entry['target_type']
        if '.' in target_id:
            target_id = target_id.split('.')[0]
        promotion_target = mongo_db[target_type].find_one({'id':int(target_id)})
        if promotion_target is not None:
            if promotion_target.get('groups') is not None:
                for perm, roles in promotion_target.get('groups').items():
                    if roles is None:
                        continue
                    new_permissions = [[role_lookup[str(role).lower()], 'entry', promotion_entry['entry_id'], perm] for role in roles if role_lookup.get(str(role)) is not None]
                    permission_csv_writer.writerows(new_permissions)
                    if perm == 'modify':
                        ## Add the delete permission as well
                        delete_perms = [[role_lookup[str(role).lower()], 'entry', promotion_entry['entry_id'], 'delete'] for role in roles if role_lookup.get(str(role)) is not None]
                        permission_csv_writer.writerows(delete_perms)
            else:
                continue

def main(mongo_db=None, role_lookup=None, entry_id=None):
    histories = [x for x in mongo_db.history.find()]
    promotion_mapping = {'alert':'event', 'event':'incident', 'dispatch':'intel'}
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')

    permission_csv = open(f'{staging_directory}/promotion_entry_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])
    
    promotion_csv = open(f'{staging_directory}/promotions.csv','w+')
    field_names = ["p0_id", "p0_type", "p1_id", "p1_type", "created_date", "modified_date"]
    promotion_writer = csv.DictWriter(promotion_csv, fieldnames=field_names, dialect='unix', delimiter='\t', quotechar="'")
    promotion_writer.writeheader()

    promotion_entries_csv = open(f'{staging_directory}/promotion_entries.csv','w+')
    field_names = ["owner", "entry_id", "target_type", "target_id", "created_date", "modified_date", "parsed", "entry_data", "entryclass"]
    promotion_entries_writer = csv.DictWriter(promotion_entries_csv, fieldnames=field_names, dialect='unix', delimiter='\t', quotechar="'")
    promotion_entries_writer.writeheader()
    
    for from_element, to_element in promotion_mapping.items():
        promoted_to = {}
        scot3_promoted_to_element_count = mongo_db[to_element].count_documents({})
        scot3_promoted_to = mongo_db[to_element].find()
        errors = []
        orig_promoted_to_length = len(promoted_to)
        for promoted_to_element in scot3_promoted_to:
            promoted_from_elements = promoted_to_element['promoted_from']
            for promoted_from_element in promoted_from_elements:
                if promoted_to.get(promoted_from_element) is None:
                    promoted_to[promoted_from_element] = {"type": to_element, "id": promoted_to_element['id'], "when":promoted_to_element['created'], "who": promoted_to_element["owner"]}
                else:
                    continue
        promoted_history = [x for x in histories if 'promoted {from_element}' in x.get('what').lower()]
        mismatches = []
        count = 0
        for h in promoted_history:
            if h.get('target').get('type') == from_element:
                to_string = re.match(fr"promoted {from_element} to {to_element} (?P<to_string>.*)", h['what'])
                to_string = to_string.groups()[0]
                to_element_id = int(to_string)
                from_element_id = h.get('target').get('id')
                if promoted_to.get(from_element_id) is not None and promoted_to.get(from_element_id).get('id') == to_element_id and promoted_to.get(from_element_id).get('type') == to_element:
                    promoted_to[from_element_id]['when'] = h.get('when')
                    promoted_to[from_element_id]['who'] = h.get('who')
                    count += 1
                else:
                    mismatches.append(h.get('when'))
            elif h.get('target').get('type') == to_element:
                from_string = re.match(fr"promoted {from_element}\(?s?\)? (?P<from_string>.*) to an? {to_element}", h['what'])
                if from_string is not None:
                    # parse the alert strings
                    from_string = from_string.groups()[0]
                    try:
                        from_ids = [int(x) for x in from_string.split(',')]
                    except Exception as e:
                        from_string = from_string.replace('[','').replace(']','')
                        if from_string != '':
                            from_ids = [int(x) for x in from_string.split(',')]
                    for from_id in from_ids:
                        if promoted_to.get(from_id) is not None and promoted_to.get(from_id).get('id') == h.get('target').get('id') and promoted_to.get(from_id).get('type') == to_element:
                            promoted_to.get(from_id)['when'] = h.get('when')
                            promoted_to.get(from_id)['who'] = h.get('who')
                            count += 1
                        else:
                            mismatches.append(h.get('when'))

        scot3_child_entry_count = mongo_db.entry.count_documents({'$and':[{'parent':{'$ne':0}}, {'class':{'$eq':'entry'}}]})
        scot3_child_entries = mongo_db.entry.find({'$and':[{'parent':{'$ne':0}}, {'class':{'$eq':'entry'}}]})
        for entry in scot3_child_entries:
            if entry.get('metadata') is not None and entry.get('metadata').get(from_element) is not None and isinstance(entry.get('metadata').get(from_element), dict) is True:
                _id = entry['target']['id']
                _type = entry['target']['type']
                from_id = entry['metadata'][from_element]['id']
                if promoted_to.get(from_id) is not None and promoted_to.get(from_id).get('type') == to_element and promoted_to.get(from_id).get('id') == _id:
                    promoted_to[from_id]['when'] = entry['created']
                    count += 1
                else:
                    mismatches.append(entry['created'])

        bulk_promotions = []
        bulk_promotion_entries = {}
        db_promotion_entries = []
        for from_id, p_object in promoted_to.items():
            promotion = {"p0_id":from_id, "p0_type":from_element, "p1_id":p_object['id'], "p1_type":p_object['type'], "created_date": datetime.fromtimestamp(p_object['when']).astimezone(timezone.utc).replace(tzinfo=None), "modified_date": datetime.fromtimestamp(p_object['when']).astimezone(timezone.utc).replace(tzinfo=None)}
            if bulk_promotion_entries.get(f"{p_object['type']}-{p_object['id']}") is None:
                _key = f"{p_object['type']}-{p_object['id']}"
                bulk_promotion_entries[_key] = {}
                bulk_promotion_entries[_key]['promotion_sources'] = [{"id":from_id, "type":from_element}]
                bulk_promotion_entries[_key]['dates'] = [p_object['when']]
            else:
                _key = f"{p_object['type']}-{p_object['id']}"
                bulk_promotion_entries[_key]['promotion_sources'].append({"id":from_id, "type":from_element})
                bulk_promotion_entries[_key]['dates'].append(p_object['when'])
            bulk_promotions.append(promotion)
        for _key, v in bulk_promotion_entries.items():
            target_type, target_id = _key.split('-')
            v['dates'].sort()
            promotion_entry = {'owner': 'scot-admin', 'entry_id': entry_id, 'target_type':target_type, 'target_id': target_id, 'entryclass': 'promotion', "created_date": datetime.fromtimestamp(v['dates'][0]).astimezone(timezone.utc).replace(tzinfo=None), 'modified_date':datetime.fromtimestamp(v['dates'][-1]).astimezone(timezone.utc).replace(tzinfo=None),  'parsed':1, 'entry_data': json.dumps({'promotion_sources':v['promotion_sources']})}
            entry_id += 1
            db_promotion_entries.append(promotion_entry)

        promotion_writer.writerows(bulk_promotions)
        promotion_entries_writer.writerows(db_promotion_entries)
        write_promotion_entry_permissions(mongo_db=mongo_db, promotion_entries=db_promotion_entries, role_lookup=role_lookup, permission_csv_writer=permission_csv_writer) 
    promotion_csv.close()
    permission_csv.close()
    promotion_entries_csv.close()
