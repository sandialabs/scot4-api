#! /bin/bash
python3 ./scot3_scot4_mongo_tsv_export.py
mysqlsh $SQL_URI --password=$SQL_PW --file ./initial_scot4_database.sql
mysqlsh $SQL_URI --password=$SQL_PW --file ./scot3_scot4_tsv_import.py

