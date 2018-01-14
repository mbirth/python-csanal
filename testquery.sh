#!/bin/sh
for f in sql/testquery*.sql; do
  echo "################"
  echo "### $f"
  echo "################"
  sqlite3 -header car2go.db3 < $f
  #sqlite3 -header -line car2go.db3 < $f
done
