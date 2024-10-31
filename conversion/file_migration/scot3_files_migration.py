import migrate_files
import migrate_cached_images
import pymongo
import os

if __name__ == "__main__":
    if (os.getenv('MONGO_DB_URI') is None or os.getenv('MONGO_DB_NAME') is None
        or os.getenv('SCOT4_URI') is None or os.getenv('SCOT_ADMIN_APIKEY') is None
    ):
        print('All of following environment variables must be set to perform file migrations:'
              + '\nMONGO_DB_URI\nMONGO_DB_NAME\nSCOT4_URI\nSCOT_ADMIN_APIKEY')
        print('You can create an admin api key by logging into the SCOT4 UI as scot-admin, or by running the '
                + '"update_admin_password_and_api_key.py" script in the extra_migration directory')
        exit(1)
    mongo_session = pymongo.MongoClient(os.getenv('MONGO_DB_URI'))[os.getenv('MONGO_DB_NAME')]
    migrate_files.main(mongo_db=mongo_session)
    migrate_cached_images.main()
