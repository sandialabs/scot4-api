import csv
import os
import tqdm
from datetime import datetime
from datetime import timezone

def main(mongo_db=None):
    staging_directory = os.getenv('SCOT_MIGRATION_STAGING_DIRECTORY')
    role_lookup = {}
    with open(f'{staging_directory}/roles.csv','w+') as role_csv:
        writer = csv.writer(role_csv, dialect='unix', delimiter='\t', quotechar="'")
        writer.writerow(['role_id', 'name', 'description', 'created', 'modified'])
        groups = mongo_db.entry.distinct('groups') 
        unique_roles = []
        for x in groups:
            for k,v in x.items():
                if isinstance(v,list):
                    for y in v:
                        if isinstance(y,str):
                            unique_roles.append(y.lower())
                        elif isinstance(y,dict):
                            unique_roles.append(y['id'].lower())
                elif isinstance(v,str):
                    unique_roles.append(v.lower())
                else:
                    continue
        unique_roles = list(set(unique_roles))
        for count, role in enumerate(tqdm.tqdm(unique_roles)):
            if role == '':
                continue
            role_row = [count+3, role, 'migrated from SCOT3', datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None), datetime.fromtimestamp(0).astimezone(timezone.utc).replace(tzinfo=None)] #Using an offset of 3 since we have two default groups: admin and everyone, created by default and taking up role ids 1 & 2 respectively
            writer.writerow(role_row)
            role_lookup[role] = count+3

    return role_lookup

if __name__ == "__main__":
    main()
