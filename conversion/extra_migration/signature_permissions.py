from app.models import Signature, Permission, Role
import requests
import os
import json
import traceback
from datetime import datetime
import tqdm
import pprint
from multiprocessing import Pool

def main(db_session):
    """
    This script assigns a role read, write, and create permissions to every
    signature, since signatures had no permissions in SCOT3. Defaults to adding
    the "everyone" permission to all signatures.
    """
    role_assign = os.getenv('SIGNATURE_ROLE', 'everyone')
    role_lookup = {x.name:x.id for x in db_session.query(Role).all()}
    sig_map = {x[1]:x[0] for x in db_session.query(Signature.id, Signature.name).all()}
    bulk_array = []
    print('Assigning access to all signatures to role "%s"' % role_assign)
    for sig, _id in tqdm.tqdm(sig_map.items()):
        roles = [role_assign]
        read_permissions = [{'role_id':role_lookup[role_assign], 'target_type':'signature', 'target_id': _id, 'permission':'read'} for role in roles if role_lookup.get(str(role)) is not None]
        write_permissions = [{'role_id':role_lookup[role_assign], 'target_type':'signature', 'target_id': _id, 'permission':'modify'} for role in roles if role_lookup.get(str(role)) is not None]
        delete_permissions = [{'role_id':role_lookup[role_assign], 'target_type':'signature', 'target_id': _id, 'permission':'delete'} for role in roles if role_lookup.get(str(role)) is not None]
        bulk_array.extend(read_permissions)
        bulk_array.extend(write_permissions)
        bulk_array.extend(delete_permissions)
    db_session.bulk_insert_mappings(Permission, bulk_array)
    db_session.commit()
    bulk_array.clear()
    print('Assigned permissions to %s signatures' % len(sig_map))

if __name__ == "__main__":
    main()
