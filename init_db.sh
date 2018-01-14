#!/bin/sh
#rm car2go.db3
sqlite3 car2go.db3 < sql/dbschema.sql
