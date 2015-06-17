#!/usr/bin/env node

/*
 * Read a newline-delimited stream of GeoJSON features,
 * write a valid GeoJSON FeatureCollection.
 */
var geojsonstream = require('geojson-stream')
var ndjson = require('ndjson')

process.stdin
.pipe(ndjson.parse())
.pipe(geojsonstream.stringify())
.pipe(process.stdout)
