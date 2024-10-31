import requests
import os
from pymongo import MongoClient
import json
import traceback
from datetime import datetime
import tqdm
import pprint
import pathlib

def main(mongo_db=None):
    if os.getenv('SCOT_FILES_DIR') is None:
        print('To migrate files from SCOT3, set the "SCOT_FILES_DIR" environment variable.\n'
              + 'You must also set "SCOT3_FILE_PREFIX" if the files were previously stored '
              + 'somewhere other than /opt/scotfiles/ in SCOT3')
        return
    file_map = (os.getenv('SCOT3_FILE_PREFIX', '/opt/scotfiles/'), os.getenv('SCOT_FILES_DIR'))
    scot4_api_key = os.getenv('SCOT_ADMIN_APIKEY')
    scot4_uri = os.getenv('SCOT4_URI')
    scot3_file_count = mongo_db.file.count_documents({})
    scot3_files = mongo_db.file.find()
    total_files_existing = []
    total_non_existing_files = []
    error_files = []
    print('Migrating files from %s' % file_map[1])
    with tqdm.tqdm(total=scot3_file_count) as pbar:
        migrated_files = 0
        for _file in scot3_files:
            try:
                file_path = _file.get('directory')
                file_name = _file.get('filename')
                if _file.get('entry_target') is None:
                    target_id = _file.get('target')['id']
                    target_type = _file.get('target')['type']
                else:
                    target_id = _file.get('entry_target')['id']
                    target_type = _file.get('entry_target')['type']
                full_file_path = f"{file_path}/{file_name}"
                full_file_path = full_file_path.replace(file_map[0], file_map[1])
                is_file_exists = pathlib.Path(full_file_path).is_file()
                if is_file_exists is True:
                    e = requests.post(f'{scot4_uri}/api/v1/file/', verify=False, files={'file': (file_name, open(full_file_path, 'rb'), 'migrated-from-scot3')}, headers={'Authorization': f'apikey {scot4_api_key}', 'target_id': str(target_id), 'target_type': target_type})
                    migrated_files += 1
                    #print(e.text)
                else:
                    print(f"{full_file_path} does not exist")
            except Exception:
                print(f"ERROR: Problem in file upload: {traceback.format_exc()}")
                error_files.append(_file)
            pbar.update(1)
    print('Migrated %s files' % migrated_files)
