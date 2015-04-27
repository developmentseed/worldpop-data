#!/usr/bin/env bash

mkdir -p shapes
mkdir -p tiles

for i in $(ls $1/*.tif) ; do scripts/vectorize.sh $i 1 worldpop shapes ; done

scripts/merge.sh shapes shapes/population.shp
scripts/merge.sh shapes/coverage shapes/coverage.shp

mapnik-shapeindex.js -d 12 shapes/population.shp

scripts/tiles.js shapes/population.shp tiles/population.mbtiles population 10 12
scripts/tiles.js shapes/coverage.shp tiles/coverage.mbtiles coverage 0 22
