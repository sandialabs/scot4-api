from app.db.session import SessionLocal
from app import crud
from app.models import User
import os

def main(db_session):
    new_admin_pw = os.getenv('SCOT_ADMIN_PASSWORD')
    new_admin_apikey = os.getenv('SCOT_ADMIN_APIKEY')
    db_obj = db_session.query(User).filter(User.username=='scot-admin').one_or_none()
    if new_admin_pw:
        update_dict={'username':'scot-admin', 'password':os.environ['SCOT_ADMIN_PASSWORD'])
        crud.user.update(db_session=db_session, db_obj=db_obj, obj_in=update_dict)
    else:
        print('SCOT_ADMIN_PASSWORD not set, not resetting scot-admin password')
    if new_admin_apikey:
        first_user_flair_api_key = {"key": os.getenv('SCOT_ADMIN_APIKEY'), "owner": "scot-admin", "active": True}
        crud.apikey.create(
                db_session=db_session,
                obj_in=first_user_flair_api_key)
    else:
        print('SCOT_ADMIN_APIKEY not set, not creating a new admin api key')
    db_session.commit()

if __name__ == '__main__':
    db_session = SessionLocal()
    main(db_session)
