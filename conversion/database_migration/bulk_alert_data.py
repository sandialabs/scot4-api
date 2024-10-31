import os
import csv
import tqdm
import json

def main(mongo_db=None):
    schema_id_map = {}
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    scot3_alertgroup_count = mongo_db.alertgroup.count_documents({})
    scot3_alertgroups = mongo_db.alertgroup.find()
    _id = 1
    with open(f'{staging_directory}/alertgroup_schema_keys.csv', 'w+') as alertgroup_schema_keys_csv:
        writer = csv.writer(alertgroup_schema_keys_csv, dialect='unix', delimiter="\t", quotechar="'")
        writer.writerow(['schema_key_name', 'alertgroup_id', 'schema_key_order', 'schema_key_id'])
        with tqdm.tqdm(total=scot3_alertgroup_count) as pbar:
            bulk_array = []
            for alertgroup in scot3_alertgroups:
                alerts = mongo_db.alert.find({'alertgroup':alertgroup['id']})
                schema_keys = set([])
                for alert in alerts:
                    schema_keys.update([k.lower() for k in alert['data'].keys()])
                new_schema_keys = [[x.lower(), alertgroup['id'], c] for c,x in enumerate(schema_keys) if (x.lower() != '_raw' and x.lower() !='columns' and x.lower() != 'search')]
                for schema_key_iter in new_schema_keys:
                    schema_key_iter.append(_id)
                    schema_key_name = schema_key_iter[0]
                    alertgroup_id = schema_key_iter[1]
                    _key = f"{schema_key_name}-{alertgroup_id}"
                    schema_id_map[_key] = _id
                    writer.writerow(schema_key_iter)
                    _id += 1
                pbar.update(1)
    scot3_alerts = mongo_db.alert.find()
    scot3_alert_count = mongo_db.alert.count_documents({})
    # initialize csv file
    with tqdm.tqdm(total=scot3_alert_count) as pbar:
        with open(f'{staging_directory}/alert_data.csv', 'w+') as alert_data_csv:
            writer = csv.writer(alert_data_csv, dialect='unix', delimiter="\t", quotechar="'")
            for alert in scot3_alerts:
                alert_datas = transform_alert(alert=alert, schema_id_map=schema_id_map)
                writer.writerows(alert_datas)
                pbar.update(1)

def transform_alert(alert=None, schema_id_map=None):
    alert_datas = []
    # First transform alert['data'] and alert['data_with_flair'] dictionaries to only have lowercase keys. This will eliminate duplicate keys 
    alert['data'] = {k.lower(): v for k,v in alert['data'].items()}
    alert['data_with_flair'] = {k.lower(): v for k,v in alert['data_with_flair'].items()}
    alertgroup_id = alert['alertgroup']
    unique_keys = set(list(alert['data'].keys()) + list(alert['data_with_flair'].keys()))
    for c,k in enumerate(unique_keys):
        if k =='columns' or k =='search' or k=='_raw':
            # We don't care about these columns because they should not show up in an alertgroup table
            continue
        else: 
            # Get the schem key id from the map we created beforehand
            schema_id = schema_id_map.get(f"{k}-{alertgroup_id}")
            if schema_id is None:
                continue
            else:
                data_value = alert['data'].get(k)
                data_value_flaired = alert['data_with_flair'].get(k)
                data_value = json.dumps(data_value)
                data_value_flaired = json.dumps(data_value_flaired)
                alert_data = [data_value, data_value_flaired, schema_id , alert['id']]
                alert_datas.append(alert_data)
    return alert_datas
