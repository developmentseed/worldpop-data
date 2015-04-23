#!/usr/bin/env bash

if [[ $# -le 1 ]] ; then
    echo "Usage: $0 inputDir outputFile.shp"
    exit 0
fi

INPUT=$1
OUTPUT=$2

for i in $(ls $INPUT/*.shp)
do
  if [ -f "$OUTPUT" ]
  then
    echo "Merging $i into $OUTPUT"
    ogr2ogr -f 'ESRI Shapefile' -t_srs EPSG:4326 -update -append $OUTPUT $i -nln `basename $OUTPUT .shp`
  else
    echo "Copying $i as $OUTPUT"
    ogr2ogr -f 'ESRI Shapefile' -t_srs EPSG:4326 $OUTPUT $i
  fi
done


