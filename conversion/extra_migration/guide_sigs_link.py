from app.models import Link, Guide, Signature
from app.db.session import SessionLocal
import datetime
import tqdm
import os

def main(db_session):
    """
    This script tries to link guides to their appropriate signature, optionally
    creating new signatures if there isn't one already for the guide.
    """
    scot_guides = db_session.query(Guide).all()
    bulk_array = []
    print('Linking guides with signatures of the same name')
    if os.getenv('NO_CREATE_GUIDE_SIGS'):
        print('NO_CREATE_GUIDE_SIGS set, new signatures will not be created if a guide exists without a signature')
    else:
        print('NO_CREATE_GUIDE_SIGS not set, new signatures will be created for guides without a signature')
    links_created = 0
    sigs_created = 0
    for guide in tqdm.tqdm(scot_guides):
        applies_to = guide.data.get('applies_to') # This is the SCOT3 assignment
        if applies_to is not None:
            for sig in applies_to:
                if 'Splunk Alert' in sig:
                    sig = sig.replace('Splunk Alert: ','')
                    res = db_session.query(Signature).filter(Signature.name == sig).all()
                    if res:
                        for result in res:
                            new_link = {'v0_type':'signature',
                                        'v0_id':result.id,
                                        'v1_type':'guide',
                                        'v1_id':guide.id,
                                        'created': guide.created}
                            bulk_array.append(new_link)
                            links_created += 1
                    # This guide had alerts it applied to, but no signature
                    elif os.getenv("NO_CREATE_GUIDE_SIGS") is None:
                        sig_create = SignatureCreate(
                            name=sig,
                            description="Autogenerated by SCOT4 migration script for guide %s" % guide.id,
                            status='active')
                        new_sig = crud.signature.create(db_session=db_session, obj_in=sig_create)
                        new_link = {'v0_type':'signature',
                                    'v0_id':new_sig.id,
                                    'v1_type':'guide',
                                    'v1_id':guide.id}
                        bulk_array.append(new_link)
                        links_created +=1
                        sigs_created += 1
    db_session.bulk_insert_mappings(Link, bulk_array)
    db_session.commit()
    print('%s guides linked to signatures' % guides_created)
    if sigs_created > 0:
        print('%s new signatures created for guides' % sigs_created)

if __name__ == "__main__":
    db_session = SessionLocal()
    main(db_session)
