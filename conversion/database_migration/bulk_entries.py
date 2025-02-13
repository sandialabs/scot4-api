import json
import os
import pymongo
import csv
from datetime import datetime
from datetime import timezone
import tqdm
import nh3
from conversion_utilities import write_tag_source_links, write_permission


sanitize_attributes = {'a': set(['href, hreflang']),
                       'bdo': set(['dir']),
                       'blockquote': set(['cite']),
                       'col': set(['align, char, charoff, span']),
                       'colgroup': set(['align, char, charoff, span']),
                       'del': set(['cite', 'datetime']),
                       'hr': set(['align', 'size', 'width']),
                       'img': set(['align', 'alt', 'src', 'height', 'width']),
                       'ins': set(['cite', 'datetime']),
                       'ol': set(['start']),
                       'q': set(['cite']),
                       'table': set(['align', 'char', 'charoff', 'summary']),
                       'tbody': set(['align', 'char', 'charoff']),
                       'td': set(['align', 'char', 'charoff', 'colspan', 'headers', 'rowspan']),
                       'tfoot': set(['align', 'char', 'charoff']),
                       'thead': set(['align', 'char', 'charoff', 'colspan', 'headers', 'rowspan', 'scope']),
                       'tr': set(['align', 'char', 'charoff']),
                       'span': set(['data-entity-value', 'data-entity-type', 'class'])
                       }


sanitize_tags = set(['a', 'abbr', 'acronym', 'area', 'article', 'aside',
                     'b', 'bdi', 'bdo', 'blockquote', 'br', 'caption', 'center',
                     'cite', 'code', 'col', 'colgroup', 'data', 'dd', 'del', 'details',
                     'dfn', 'div', 'dl', 'dt', 'em', 'figcaption', 'figure', 'footer', 'h1',
                     'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'i', 'img', 'ins', 'kbd',
                     'kbd', 'li', 'map', 'mark', 'nav', 'ol', 'p', 'pre', 'q', 'rp', 'rt', 'rtc', 'ruby',
                     's', 'samp', 'small', 'span', 'strike', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody',
                     'td', 'th', 'thead', 'time', 'tr', 'tt', 'u', 'ul', 'var', 'wbr'])


def sanitize_attribute_filter(element, attribute, value):
    if element == 'span' and attribute == 'class' and value.startswith('entity'):
        return "entity"
    elif element == 'span' and attribute == 'class' and not value.startswith('entity'):
        return None
    else:
        return value


def sanitize_html(html: str):
    # bypassing sanitization so we don't lose data during migration
    return html
    #if isinstance(html, str):
    #    return nh3.clean(html, tags=sanitize_tags, attributes=sanitize_attributes, attribute_filter=sanitize_attribute_filter)
    #else:
    #    return ""



def main(mongo_db=None, role_lookup=None):
    last_entry_id = None
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    scot3_entry_count = mongo_db.entry.count_documents({})
    scot3_entries = mongo_db.entry.find()
    permission_csv = open(f'{staging_directory}/entry_permissions.csv','w+')
    permission_csv_writer = csv.writer(permission_csv, dialect='unix', delimiter='\t', quotechar="'")
    permission_csv_writer.writerow(['role_id', 'target_type', 'target_id', 'permission'])
    with open(f'{staging_directory}/entries.csv','w+') as entry_csv:
        writer = csv.writer(entry_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['entry_id', 'parent_entry_id', 'tlp', 'owner', 'created_date', 'modified_date', 'target_type', 'target_id', 'entryclass', 'parsed',  'entry_data'])
        with tqdm.tqdm(total=scot3_entry_count) as pbar:
            bulk_array = []
            for entry in scot3_entries:
                if entry.get('target') is None or entry['target'].get('type') is None:
                    pbar.update(1) # Malformed data
                    continue
                if entry['target']['type'] == 'alert' or entry['target']['type'] == 'alertgroup' or entry['target']['type'] == 'feed':
                    pbar.update(1)
                    continue
                if entry.get('metadata') is not None and entry.get('metadata').get('alert') is not None:
                    pbar.update(1) # These are entries that we are replacing with promotion entries. 
                    continue
                tlp = entry.get('tlp')
                if tlp is None:
                    tlp = 'unset'
                elif tlp =='amber+strict':
                    tlp = 'amber_strict'
                if entry['class'] == 'entry' or entry['class'] == 'summary' or entry['class'] == 'task':
                    parent_id = "NULL"
                    if entry.get('parent') != 0 and entry.get('parent') is not None:
                        parent_id = entry.get('parent')
                    if entry['class'] == 'task' and entry.get('metadata') and entry['metadata'].get('task'):
                        entry_data = json.dumps({'html':sanitize_html(entry['body']), 'flaired_html':sanitize_html(entry['body_flair']), 'plain_text':sanitize_html(entry['body_plain']), 'status':entry['metadata']['task'].get('status'), 'task_time':entry['metadata']['task'].get('when'), 'assignee':entry['metadata']['task'].get('who')})
                    else:
                        entry_data = json.dumps({'html':sanitize_html(entry['body']), 'flaired_html':sanitize_html(entry['body_flair']), 'plain_text':sanitize_html(entry['body_plain'])})
                    new_entry = [ entry['id'], parent_id, tlp, entry['owner'], datetime.fromtimestamp(entry['created']).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(entry['updated']).astimezone(timezone.utc).replace(tzinfo=None), entry['target']['type'], entry['target']['id'], entry['class'], 1, entry_data ]
                    last_entry_id = entry['id']
                    writer.writerow(new_entry)
                    write_permission(thing=entry, thing_type='entry', role_lookup=role_lookup, permission_csv_writer=permission_csv_writer)
                pbar.update(1)
    permission_csv.close()
    return last_entry_id+1 # Need the next available ID of the entries for the promotion entries, which are a new concept in SCOT4. 

if __name__=="__main__":
    mongo_session = pymongo.MongoClient()['scot-prod']
    main(mongo_session)
