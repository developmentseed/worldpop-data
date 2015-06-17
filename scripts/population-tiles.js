#!/usr/bin/env node
var path = require('path')
var debug = require('debug')('wp')
var queue = require('queue-async')
var split = require('split')
var through = require('through2')
var ndjson = require('ndjson')
var vtgeojson = require('vt-geojson')
var worldpop = require('worldpop')
var tilebelt = require('tilebelt')
var area = require('turf-area')
var grid = require('turf-square-grid')

var uri = process.argv[2]
uri = 'mbtiles://' + path.resolve(uri)

process.stdin
  .pipe(through(function (chunk, _, next) {
    debug('line')
    next(null, chunk)
  }))
  .pipe(split())
  .pipe(through.obj(processTile))
  .pipe(ndjson.stringify())
  .pipe(process.stdout)

function processTile (tile, _, next) {
  var self = this
  tile = tile.toString().split(' ').map(Number)
  if (tile.length !== 3) { return next() }
  debug('processing', tile)

  var sidelength = Math.sqrt(area(tilebelt.tileToGeoJSON(tile)))
  var boxes = grid(
    tilebelt.tileToBBOX(tile),
    Math.ceil(sidelength / 2000),
    'kilometers'
  ).features
  var q = queue()
  var source = through.obj()
  boxes.forEach(function (feature) {
    q.defer(aggregatePopulation, source, feature)
  })
  q.awaitAll(function (err, features) {
    if (err) { console.error(tile, err) }
    debug('results', tile, features.length)
    features
    .filter(function (feature) { return feature.properties.totalPopulation > 0 })
    .forEach(function (feature) { self.push(feature) })

    next()
  })
  vtgeojson(uri, [tile], 'population').pipe(source)
}

function density (feature) {
  return feature.properties.density / 10000
}

function aggregatePopulation (source, feature, cb) {
  worldpop({
    source: source,
    min_zoom: 11,
    max_zoom: 11,
    polygon: feature,
    density: density
  }, function (err, properties) {
    if (err) { return cb(err) }
    if (properties.totalPopulation > 0) {
      properties.density = 10000 * properties.totalPopulation / properties.totalArea
      feature.properties = properties
    }
    cb(null, feature)
  })
}
