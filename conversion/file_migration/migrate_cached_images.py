import requests
import os
from pymongo import MongoClient
import json
import traceback
from datetime import datetime
import tqdm
import pprint
import pathlib
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def rewrite_cached_images(html, flaired_html, entry_id):
    scot4_api_key = os.getenv('SCOT_ADMIN_APIKEY')
    scot4_uri = os.getenv('SCOT4_URI')
    cached_images = os.getenv('SCOT_CACHED_IMAGES_DIR')
    try:
        cached_image_match_uncompiled = r'\"/cached_images/(?P<year>\d{4})\/(?P<type>[A-Za-z]+)/(?P<id>\d+)/(?P<filename>[^"]*)\"'
        cached_image_match_alt_uncompiled = r'\"/cached_images/(?P<filename>[^/]*\.(?:png|PNG|jpg|JPG|jpeg|JPEG))\"'

        # Try compiling for speed up
        cached_image_match = re.compile(cached_image_match_uncompiled)
        cached_image_match_alt = re.compile(cached_image_match_alt_uncompiled)
        changed = False
        for line in html.splitlines():
            m = re.finditer(cached_image_match, line)
            for match in m:
                year = match.groupdict()['year']
                scot_type = match.groupdict()['type']
                scot_id = match.groupdict()['id']
                file_name = match.groupdict()['filename']
                file_path = f"{cached_images}/{year}/{scot_type}/{scot_id}/{file_name}"
                file_exists = pathlib.Path(file_path).is_file()
                if file_exists:
                    e = requests.post(f'{scot4_uri}/api/v1/file/', verify=False, files={'file': (file_name, open(file_path, 'rb'), 'migrated-from-scot3')}, headers={'Authorization': f'apikey {scot4_api_key}', 'target_id': str(scot_id), 'target_type': scot_type})
                    #print(e.text)
                    file_id = e.json().get('id')
                    if file_id is None:
                        print(f"ERROR: Missing file_id when uploading in entry {entry_id} and file {file_path}: {e.text}")
                        continue
                    scot4_path = f"/api/v1/file/download/{file_id}"
                    html = html.replace(match.group(0), f'\"{scot4_path}\"')
                    if flaired_html is not None:
                        flaired_html = flaired_html.replace(match.group(0), f'\"{scot4_path}\"')
                    changed = True
                    print(f"INFO: Changed Entry {entry_id} added file {file_id}")
                else:
                    print(f"WARN: Could not find file in entry {entry_id}: {file_path}")
        # If a user drag/drops an image into an entry, the html has the data embedded and 
        # the flaired_html will have the image as a path to cached_image
        # Need to cover this scenario as well
        if flaired_html is not None:
            for line in flaired_html.splitlines():
                m = re.finditer(cached_image_match_alt, line)
                for match in m:
                    file_name = match.groupdict()['filename']
                    file_path = f"{cached_images}/{file_name}"
                    file_exists = pathlib.Path(file_path).is_file()
                    if file_exists:
                        e = requests.post(f'{scot4_uri}/api/v1/file/', verify=False, files={'file': (file_name, open(file_path, 'rb'), 'migrated-from-scot3')}, headers={'Authorization': f'apikey {scot4_api_key}'})
                        #print(e.text)
                        file_id = e.json().get('id')
                        if file_id is None:
                            print(f"ERROR: Missing file_id when uploading in entry {entry_id} and file {file_path}: {e.text}")
                            continue
                        scot4_path = f"/api/v1/file/download/{file_id}"
                        flaired_html = flaired_html.replace(match.group(0), f'\"{scot4_path}\"')
                        changed = True
                        print(f"INFO: Changed Entry {entry_id} added file {file_id}")
                    else:
                        print(f"WARN: Could not find file in entry {entry_id}: {file_path}")
        if changed is False:
            return False, False
        else:
            return html, flaired_html
    except Exception:
        print(f"ERROR: Problem in image upload: {traceback.format_exc()}")
        return False, False

def main():
    if os.getenv('SCOT_CACHED_IMAGES_DIR') is None:
        print('To rewrite cached images, the "SCOT_CACHED_IMAGES_DIR" environment '
              + 'variable must be set to a copy of the old SCOT3 cached_images directory')
        return
    db_session = SessionLocal()
    count = db_session.query(Entry).count()
    limit = 100
    current_offset = 0
    converted = 0
    print('Migrating cached images from %s' % os.getenv('SCOT_CACHED_IMAGES_DIR'))
    for chunk in tqdm.tqdm(range(0, count, limit)):
        entries = db_session.query(Entry).limit(limit).offset(current_offset).all()
        for entry in entries:
            flair_html = entry.entry_data.get('flaired_html')
            html = entry.entry_data.get('html')
            entry_id = entry.id
            if html is None:
                continue
            html_result, flair_result = rewrite_cached_images(html, flair_html, entry_id)
            if html_result is not False and flair_result is not False:
                if entry.entry_data.get('plain_text') is not None:
                    entry.entry_data = {"html": html_result, "flaired_html": flair_result, "plain_text": entry.entry_data['plain_text']}
                else:
                    entry.entry_data = {"html": html_result, "flaired_html": flair_result, "plain_text": ""}
                db_session.add(entry)
                db_session.commit()
                db_session.flush()
                converted += 1
        current_offset += limit
    print('Migrated cached images from %s entries' % converted)

if __name__ == "__main__":
    main()
