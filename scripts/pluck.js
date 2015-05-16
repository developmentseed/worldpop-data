#!/usr/bin/env iojs --harmony_arrow_functions

var fs = require('fs')
var path = require('path')
var exec = require('child_process').exec

var files = process.argv.slice(2)

var dryrun = false
if (files[0] === '--dryrun') {
  dryrun = true
  files.shift()
}

dofile()

function dofile () {
  var file = files.shift()
  if (!file) return

  process.stdout.write('\n' + path.basename(file))
  var code = path.basename(file).split('-')[0]

  if (fs.existsSync(file)) {
    exec(
      '7z l ' + file + '', (err, stdout, stderr) => {
        if (err) {
          process.stdout.write('\tskipping, error listing archive: ' + JSON.stringify(err))
          return dofile()
        }

        var allFiles = stdout.toString()
          .match(RegExp(code + '[^ \t\n]+', 'g'))

        var toExtract = allFiles
        .map((f) => f.match(/.*([0-9]+).*adj.*\.tif$/))
        .filter((match) => (match !== null && match.length > 0))
        .sort((a, b) => Number(b[1]) - Number(a[1]))
        .map((match) => match[0])

        if (toExtract.length === 0) {
          process.stdout.write('\tskipping, no suitable TIFs: ')
          process.stdout.write(allFiles.join(','))
          return dofile()
        } else if (toExtract.length > 1) {
          var pph = toExtract.filter((file) => /pph/.test(file))
          if (pph.length > 0) toExtract = pph
        }

        // we got a single desired file, so extract it.
        process.stdout.write('\textracting ' + toExtract[0])

        if (dryrun) return dofile()

        exec('7z x -bd -y ' + file + ' ' + toExtract[0] + '*', (err, stdout, stderr) => {
          if (err) console.error(err)
          else process.stdout.write('\tcomplete\n')
          dofile()
          // fs.unlink(file, function () { process.stdout.write('deleted ' + file) })
        })
      }
    )
  }
}
