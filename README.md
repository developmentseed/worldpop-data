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

**NOTE:** The `vectorize` loop above assumes that all of the tif files have
data in the same units - ideally, people per hectare.  However, for some
countries, the older WorldPop datasets that are available only have people per
*pixel*.  My suggestion is to assess the size of a pixel in those cases, and
then change the second parameter to `vectorize.sh` (`1` above) to the
appropriate scale factor.
