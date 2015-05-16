# worldpop-data

Data processing pipeline for the worldpop project.  Takes Worldpop GeoTIFF
files of population data and generates an mbtiles file of Mapbox Vector tiles
containing polygons of constant population density.

Original data available at [worldpop.org.uk](http://www.worldpop.org.uk/).

## Prerequisites:
 - GDAL
 - GNU Parallel
 - Postgres and PostGIS

## Workflow:

Assuming you've put the specific TIF (and associated metadata) files you want
into `data/`, do the following from the root of this repo:

```bash
mkdir temp
mkdir shapes
mkdir tiles

ls data/*.tif | parallel scripts/vectorize.sh {} 1 density shapes

scripts/setup-pg.sh
ls shapes/*.shp | scripts/merge.sh population
ls shapes/coverage/*.shp | scripts/merge.sh coverage
```

**NOTE:** The `vectorize` loop above assumes that all of the tif files have
data in the same units - ideally, people per hectare.  However, for some
countries, the older WorldPop datasets that are available only have people per
*pixel*.  My suggestion is to assess the size of a pixel in those cases, and
then change the second parameter to `vectorize.sh` (`1` above) to the
appropriate scale factor.

Alternatively, you can do this in one fell swoop with:

```bash
scripts/run.sh your_data/*.tif
```

## Make Tiles

At this point, the data is in the `worldpop` postgres database.  Open up
`pg-source.tm2source` in Mapbox Studio, modify the postgres username
in both the `population` and `coverage` layers, and you should be good to go.
You can now upload the tiles to Mapbox or export an `mbtiles` file.

