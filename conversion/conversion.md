# SCOT3 to SCOT4 Conversion Utilities

This directory contains scripts for migrating data from version 3 of SCOT to version 4. They are grouped into three categories: database migrations, file migrations, and extra (optional) migrations. Three bash shell scripts have been provided for you to run the applicable migrations in each category.

## Necessary tools to run conversion
You will need the following installed to run conversions:
- python 3.11 with the contents of requirements-test.txt from this repo installed via pip
- mysql-shell

## Database Conversion
This set of scripts migrates the core database data to the SCOT4 database by pulling data directly from the SCOT3 mongodb database. Almost all SCOT3 installations migrating to SCOT4 will want to do this. The `database_conversion.sh` script will run all of the necessary scripts for you.

The following environment variables should be set when running `database_conversion.sh`:
 - MONGO_DB_URI - the URI used to connect to the SCOT3 mongodb database
 - MONGO_DB_NAME - the name of the SCOT3 mongodb database
 - SQL_URI - the URI used to connect to the SCOT4 SQL database
 - SQL_PW - the password used to connect to the SCOT4 SQL database
 - SCOT_MIGRATION_STAGING_DIRECTORY (optional) - the directory used to stage intermediate files for the conversion (created if does not exist, default /data/scot4_migration_sync/)
 
## Extra Migrations
This set of scripts contains useful entries that are not necessarily required, but which will ease the transition from SCOT3 to SCOT4.

### Signature Migrations
One of the primary ways that SCOT4 differs from SCOT3 is that guides must be linked to alerts by way of a signature. In SCOT4, signatures more explicitly represent the rules that generate alerts, so guides are linked to specific signatures, and those signatures are then linked to alerts when they fire.

Because of this, in order for guides for new and past alerts to be linked properly, each must be linked to a signature. The script `guide_sigs_link.py` will attempt to link guides to signatures by name or create a new signature for a guide if there isn't already a signature with the same name. Likewise, `link_alerts_signatures.py` will attempt to link all existing alerts with a signature as if those alerts had just been generated. `signature_permissions.py` will also fix permissions on existing signatures (since signatures didn't have permissions in SCOT3).

If you would like to perform all of these extra signature migrations steps, run the `signature_conversion.sh` script.

The following environment variables should be set when running `signature_conversion.sh`:
 - SQLALCHEMY_DATABASE_URI - set to the SCOT4 database URI, as if running the SCOT4 API
 - PYTHONPATH - set to include the src/ directory of the SCOT4 API (the scripts borrow code from the API to run)
 
### Admin Migration
By default, the SCOT4 migration creates a user named `scot-admin` to be the initial superuser for SCOT. You can give this user a password and an API key by setting the `SCOT_ADMIN_PASSWORD` and/or `SCOT_ADMIN_APIKEY` environment variables respectively, then running the `extra_migration/update_admin_password_and_api_key.py` script.

The following environment variables should be set when running `update_admin_password_and_api_key.py`:
 - SQLALCHEMY_DATABASE_URI - set to the SCOT4 database URI, as if running the SCOT4 API
 - PYTHONPATH - set to include the src/ directory of the SCOT4 API (the script borrows code from the API to run)
 
## File Conversion
Finally, if you uploaded files to SCOT3 and wish to migrate them to SCOT4, they must be migrated separately. This also applies to cached images in entries that were downloaded and subsequently hosted through SCOT. These scripts upload the files and cached images to the SCOT4 file store and also rewrite existing entries to point to the new files.

Before files and images can be migrated, **you must configure a file storage mechanism on the SCOT4 instance**. This usually means that you must set up the API and frontend, and configure a file storage option through the admin panel on the frontend. Once you have done this, you can run the `file_conversion.sh` to migrate both files and cached images from SCOT3.

The following environment variables should be set when running `file_conversion.sh`:
 - MONGO_DB_URI - the URI of the SCOT3 mongodb database
 - MONGO_DB_NAME - the name of the SCOT3 mongodb database
 - SCOT4_URI - the base URI of the SCOT4 installation (e.g. https://scot4.example.com)
 - SCOT_ADMIN_APIKEY - a SCOT4 API key with admin priveleges (see above for one way to create one)
 - SCOT3_FILE_PREFIX (needed for file migration) - the directory under which the files were stored in the SCOT3 database, this defaults to the default in SCOT3, which was `/opt/scotfiles/`
 - SCOT_FILES_DIR (needed for file migration) - the directory on the current machine in which the old SCOT3 files are stored (with the same file structure that the SCOT3 installation had)
 - SCOT_CACHED_IMAGES_DIR (needed for cached images migration) - the directory on the current machine that contains the SCOT3 cached images in their original file structure (this is usually the /cached_images/ directory in the SCOT3 files)
