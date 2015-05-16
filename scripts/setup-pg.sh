#!/usr/bin/env bash
dropdb worldpop
createdb worldpop
psql -d worldpop -c "CREATE EXTENSION postgis;"
psql -d worldpop -c "CREATE EXTENSION fuzzystrmatch;"
psql -d worldpop -c "CREATE EXTENSION postgis_topology;"
psql -d worldpop -c "CREATE EXTENSION postgis_tiger_geocoder;"
curl https://raw.githubusercontent.com/mapbox/postgis-vt-util/master/lib.sql | psql -d worldpop

