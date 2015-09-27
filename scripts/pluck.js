#!/usr/bin/env node --harmony_arrow_functions

var fs = require('fs')
var path = require('path')
var exec = require('child_process').exec

var files = process.argv.slice(2)

dofile()

var file
function dofile (err, stdout, stderr) {
  if (err) { console.error(file, err, stdout, stderr) }

  file = files.shift()
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
      exec('7z x -bd -y ' + file + ' ' + toExtract[0], upload.bind(null, toExtract[0]))
    })
  })
}

function upload (extracted, err, stdout, stderr) {
  if (err) {
    return dofile(err, stdout, stderr)
  } else {
    console.log('\tgzipping and uploading ' + extracted)
    exec('gzip ' + extracted, function (err) {
      if (err) { return dofile(err) }
      var ready = extracted + '.gz'
      exec('aws s3 cp ' + ready + ' s3://world-pop/extracted/', deleteFiles.bind(null, file, ready))
    })
  }
}

function deleteFiles (archive, uploaded, err, stdout, stderr) {
  if (err) { console.error(file, err, stdout, stderr) }
  fs.unlink(archive, function (err) {
    if (err) { return dofile(err) }
    fs.unlink(uploaded, function (err) {
      if (err) { return dofile(err) }
      console.log('deleted ' + archive + ' and ' + uploaded)
      dofile()
    })
  })
}
