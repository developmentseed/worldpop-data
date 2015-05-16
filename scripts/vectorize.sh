#!/usr/bin/env sh

INPUT=$1
FACTOR=$2

BASE=`basename $1 .tif`
SCALED=${BASE}.x${FACTOR}.tif
POLY=${BASE}.x${FACTOR}.shp

PROPERTY=$3
OUTPUT=$4

if [[ $# -le 3 ]] ; then
    echo "Usage: $0 inputfile.tif scaleFactor outputPropertyName outputDir"
    exit 0
fi

# Scale up raster values by factor of 100.  This takes us from ppl/(100m^2) to
# ppl/km^2.
# Also set nodata to 0 so that it'll get filtered out during polygonize.
echo "Scaling up ratser data x$FACTOR."
gdal_calc.py -A $INPUT --type=Float32 --calc="A * $FACTOR" --outfile=temp/$SCALED
gdal_calc.py -A $INPUT --type=Int16 --calc="1" --outfile=temp/${BASE}.coverage.tif

# Polygonize
echo "Polygonizing."
gdal_polygonize.py temp/$SCALED -f "ESRI Shapefile" $OUTPUT/$POLY $PROPERTY $PROPERTY

mkdir -p $OUTPUT/coverage
gdal_polygonize.py temp/${BASE}.coverage.tif -f "ESRI Shapefile" $OUTPUT/coverage/${BASE}.coverage.shp

echo "Cleaning up."
rm temp/$SCALED
rm temp/${BASE}.coverage.tif

echo "Finished."
