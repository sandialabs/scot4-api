#! /bin/bash
set -e

CONVERSION_DIR=$(dirname "$0")

# Test to make sure PYTHONPATH and SQLALCHEMY_DATABASE_URI are set correctly
cd $CONVERSION_DIR/extra_migration
python3 ./test_database.py

# Do signature migrations
python3 ./guide_sigs_link.py
python3 ./signature_permissions.py
python3 ./link_alerts_signatures.py
