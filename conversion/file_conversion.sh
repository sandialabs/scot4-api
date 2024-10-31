#! /bin/bash
set -e

CONVERSION_DIR=$(dirname "$0")

# Delegate to python script
cd $CONVERSION_DIR/file_migration
python3 ./scot3_files_migration.py
