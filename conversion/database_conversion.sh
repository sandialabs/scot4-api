#! /bin/bash
set -e

CONVERSION_DIR=$(dirname "$0")
SCOT_MIGRATION_STAGING_DIRECTORY="${SCOT_MIGRATION_STAGING_DIRECTORY:-/data/scot4_migration_sync/}"

# Set up dirs
mkdir -p $SCOT_MIGRATION_STAGING_DIRECTORY/conversion_staging

# Create all TSVs from mongo data
cd $CONVERSION_DIR/database_migration
python3 ./scot3_scot4_mongo_tsv_export.py

# Tear down DB and import TSVs
mysqlsh $SQL_URI --password=$SQL_PW --file ./initial_scot4_database.sql
mysqlsh $SQL_URI --password=$SQL_PW --file ./scot3_scot4_tsv_import.py
mysqlsh $SQL_URI --password=$SQL_PW --file ./fix_parent_entry_ids.sql
