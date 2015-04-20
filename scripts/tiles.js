#!/usr/bin/env node

/**
 * Convert the given omnivore-compatible vector source into an mbtiles
 * file of vector tiles.
 */

var fs = require('fs')
var path = require('path')
var multi = require('multimeter')(process)
var tilelive = require('tilelive')
var Bridge = require('tilelive-bridge')
var _ = require('lodash')
var getMetadata = require('mapnik-omnivore').digest
require('mbtiles').registerProtocols(tilelive)

var MIN_ZOOM = 8
var MAX_ZOOM = 12
var xml = fs.readFileSync(path.join(__dirname, 'template.xml'), 'utf8')

if (process.argv.length < 4) {
  console.log('Usage: ', process.argv[0], process.argv[1], ' source.shp dest.mbtiles')
  process.exit()
}

var srcFile = path.resolve(process.argv[2])
var dsturi = 'mbtiles://' + path.resolve(process.cwd(), process.argv[3])

getMetadata(srcFile, function (err, metadata) {
  if (err) throw err

  metadata.filepath = srcFile

  // Following is from mapbox/tilelive-omnivore
  metadata.format = metadata.dstype === 'gdal' ? 'webp' : 'pbf'
  metadata.layers = metadata.layers.map(function (name) {
    return {
      layer: name,
      type: metadata.dstype,
      file: metadata.filepath
    }
  })

  metadata.minzoom = Math.max(metadata.minzoom, MIN_ZOOM)
  metadata.maxzoom = Math.min(metadata.maxzoom, MAX_ZOOM)
  var mapnikXml = _.template(xml)(metadata)

  new Bridge({ xml: mapnikXml }, function (err, source) {
    if (err) throw err

    if (process.argv[process.argv.length - 1] === 'info') {
      source.getInfo(function (err, info) {
        console.log(err, info)
        process.exit()
      })
    } else {
      multi.drop({width: 40}, function (bar) {
        tilelive.copy(source, dsturi, {
          type: 'scanline',
          minzoom: metadata.minzoom,
          maxzoom: metadata.maxzoom,
          progress: function (stats, p) {
            bar.percent(p.percentage)
          }
        }, function (err) {
          if (err) throw err
          console.log('\n\nFinished')
          process.exit()
        })
      })
    }
  })
})
