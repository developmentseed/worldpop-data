#!/usr/bin/env bash

# Import the given shapefiles into postgres db `worldpop`.
# Usage:
# ls *.shp | merge.sh tablename [--overwrite]

LAYER=$1

if [[ $2 = '--overwrite' ]] ; then
  read firstfile
  ogr2ogr -f 'PostgreSQL' PG:dbname=worldpop -t_srs EPSG:4326 \
    -overwrite -nln $LAYER $firstfile
fi

parallel ogr2ogr -f 'PostgreSQL' PG:dbname=worldpop -t_srs EPSG:4326 \
  -update -append -nln $LAYER {} <&0
