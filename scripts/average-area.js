#!/usr/bin/env node

var area = require('turf-area')
var poly = require('turf-polygon')
var gdalinfo = require('gdalinfo-json')

var args = process.argv.slice(2)
var tolerance = Number.MAX_VALUE

if (args[0] === '--tolerance') {
  tolerance = Number(args[1])
  args = args.slice(2)
}

args.forEach(function (file) {
  gdalinfo.local(file, function (err, data) {
    if (err) throw err

    var size = data.pixel_size

    var northern = data.corners_lon_lat['upper_right']
    var southern = data.corners_lon_lat['lower_right']
    var cornerAreas = [northern, southern]
    .map(function (c) {
      var x = c[0], y = c[1]
      var pixel = poly([[
        [x, y],
        [x + size[0], y],
        [x + size[0], y + size[1]],
        [x, y + size[1]],
        [x, y]
      ]])
      return area(pixel)
    })

    var avg = 0.5 * (cornerAreas[0] + cornerAreas[1])
    var pctChange = cornerAreas[1] / cornerAreas[0]
    if (Math.abs(pctChange - 1) < tolerance) {
      process.stdout.write([file, avg, pctChange].join('\n') + '\n')
    }
  })
})
