#!/usr/bin/env node --harmony_arrow_functions

var fs = require('fs')
var path = require('path')
var exec = require('child_process').exec

var files = process.argv.slice(2)

var dryrun = false

dofile()

function dofile (err) {
  if (err) {
    console.error(files[0], err)
  }
  var file = files.shift()
  if (!file) { return }
  console.log(path.basename(file))

  var code = path.basename(file).split('-')[0]

  console.log('\tdownloading')
  exec('aws s3 cp s3://world-pop/' + file + ' .', function (err, stdout, stderr) {
    if (err) { return dofile(err) }
    exec('7z l ' + file + '', (err, stdout, stderr) => {
      if (err) { return dofile(err) }

      var allFiles = stdout.toString().match(RegExp(code + '[^ \t\n]+', 'g'))

      var toExtract = allFiles
      .map(f => f.match(/.*([0-9]+).*adj.*\.tif$/))
      .filter(match => (match !== null && match.length > 0))
      .sort((a, b) => +b[1] - +a[1])
      .map(match => match[0])

      if (toExtract.length === 0) {
        return dofile(new Error('skipping, no suitable TIFs: ' + allFiles.join(',')))
      } else if (toExtract.length > 1) {
        var pph = toExtract.filter((file) => /pph/.test(file))
        if (pph.length > 0) toExtract = pph
      }

      console.log('\textracting ' + toExtract[0])

      if (dryrun) return dofile()

      exec('7z x -bd -y ' + file + ' ' + toExtract[0], (err, stdout, stderr) => {
        if (err) {
          return dofile(err)
        } else {
          console.log('\tuploading ' + toExtract[0])
          exec('gzip ' + toExtract[0], function (err) {
            if (err) { dofile(err) }
            var ready = toExtract[0] + '.gz'
            exec('aws s3 cp ' + ready + ' s3://world-pop/extracted/', (err, stdout, stderr) => {
              if (err) { console.error(file, err) }
              fs.unlink(file, function (err) {
                if (err) { return dofile(err) }
                fs.unlink(ready, function (err) {
                  if (err) { return dofile(err) }
                  console.log('deleted ' + file + ' and ' + ready)
                  dofile()
                })
              })
            })
          })
        }
      })
    })
  })
}
