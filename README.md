# worldpop-data

Data processing pipeline for the worldpop project.  Takes Worldpop GeoTIFF
files of population data and generates an mbtiles file of Mapbox Vector tiles
containing polygons of constant population density.

Original data available at [worldpop.org.uk](http://www.worldpop.org.uk/).

## Workflow:

Assuming you've put the specific TIF (and associated metadata) files you want
into `data/`, do the following from the root of this repo:

```bash
mkdir temp
mkdir shapes
mkdir tiles

for i in $(ls data/*.tif) ; do scripts/vectorize.sh $i 1 worldpop shapes ; done

scripts/merge.sh shapes temp/density.shp

scripts/tiles.js temp/density.shp tiles.worldpop.mbtiles worldpop
```
