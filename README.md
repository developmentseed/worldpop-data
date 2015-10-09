# worldpop-data

Data processing pipeline for the worldpop project.  Takes Worldpop GeoTIFF
files of population data and generates an mbtiles file of Mapbox Vector tiles
containing polygons of constant population density.

Original data available at [worldpop.org.uk](http://www.worldpop.org.uk/).

## Prerequisites:
 - [GDAL](http://www.gdal.org/)
 - Python modules: `pip install rasterio boto3`
 - vt-grid: `npm install -g vt-grid`

## From GeoTIFFs to GeoJSON:

```sh
python scripts/process.py -o OUTPUT_PREFIX INPUT1 [INPUT2 INPUT3 INPUT4 ...]
```

`INPUT1`, etc. are locations of input GeoTIFF images, again either local or on
s3. Paths ending in `.gz` will be unzipped

`OUTPUT_PREFIX` is either a local directory or an s3 uri like `s3://bucket/folder/blah`.
Resulting geojson will go here, gzipped, one per input file.

(Note: you can make this quite a bit faster using GNU Parallel.)

## From GeoJSON to vector tiles

1. Get all the GeoJSON files somewhere that you can pipe them through `gunzip` (or just unzip em all if you have plenty of space).
2. Cut the raw data into (high zoom) tiles: `cat /path/to/geojson/*.geojson.gz | gunzip | tippecanoe -z 11 -Z 11 -b 0 -l population -o worldpop-base.mbtiles`
3. Aggregate: `vt-grid worldpop-base.mbtiles worldpop.mbtiles --gridsize 1024 --aggregations 'population:areaWeightedMean(densitypph)'`
4. Upload `worldpop.mbtiles` to Mapbox (or wherever you can host/serve it), and Bob's your uncle.

