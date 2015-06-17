#!/usr/bin/env node
var path = require('path')
var cover = require('tile-cover')
var vtgeojson = require('vt-geojson')
var combine = require('turf-combine')

var uri = process.argv[2]
uri = 'mbtiles://' + path.resolve(uri)

var features = []
vtgeojson(uri, 3, 'coverage')
.on('data', function (feature) {
  features.push(feature)
})
.on('end', function () {
  var feature = combine({type: 'FeatureCollection', features: features})
  var tiles = cover.tiles(feature.geometry, {min_zoom: 11, max_zoom: 11})
  console.log(
    tiles
    .map(function (tile) { return tile.join(' ') })
    .join('\n')
  )
})

