from app import crud
from app.db.session import SessionLocal
from app.models import AlertGroup, Alert, Event, Link, Signature, Promotion
import tqdm

def main(db_session):
    sig_map = {x[1]:x[0] for x in db_session.query(Signature.id, Signature.name).all()}
    bulk_array = []
    alertgroups_assigned = 0
    print('Linking existing alertgroups to signatures of the same name')
    for sig, _id in tqdm.tqdm(sig_map.items()):
        alertgroup_matches = [x[0] for x in db_session.query(AlertGroup.id).filter(AlertGroup.subject.like(f'%{sig}%')).all()]
        alerts = [x[0] for x in db_session.query(Alert.id).filter(Alert.alertgroup_id.in_(alertgroup_matches)).all()]
        promotions = db_session.query(Promotion.p1_id, Promotion.p1_type).filter(Promotion.p0_id.in_(alerts), Promotion.p0_type == 'alert').all()
        for alertgroup_id in alertgroup_matches:
            new_link = {'v0_type':'alertgroup', 'v0_id':alertgroup_id, 'v1_type':'signature', 'v1_id':_id, 'context': 'alertgroup created from signature hits'}
            bulk_array.append(new_link)
            alertgroups_assigned += 1;
        for alert in alerts:
            new_link = {'v0_type':'alert', 'v0_id':alert, 'v1_type':'signature', 'v1_id':_id, 'context': 'alert created from signature hits'}
            bulk_array.append(new_link)
        for promotion_target in promotions:
            new_link = {'v0_type':promotion_target[1], 'v0_id':promotion_target[0], 'v1_type':'signature', 'v1_id':_id, 'context': f'{promotion_target[1].value} created from signature hits'}
            bulk_array.append(new_link)
        db_session.bulk_insert_mappings(Link, bulk_array)
        db_session.commit()
        bulk_array.clear()
        print('%s alertgroups were linked to existing signatures')

if __name__ == '__main__':
    db_session = SessionLocal()
    main(db_session)
