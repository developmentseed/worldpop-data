#!/usr/bin/env python

from os import path
from pprint import pprint
import argparse
import numpy as np
import numpy.ma as ma
import rasterio
from rasterio.warp import reproject, RESAMPLING, transform
from affine import Affine
from geojson import Polygon, Feature, FeatureCollection
from math import pi, sin, fabs, radians

wgs_r2 = 6378137 * 6378137
dst_crs = {'init': 'epsg:4326'}


def dest_affine(affine, src_crs, shape):
    corners = [(0, 0), (0, shape[0]), (shape[1], shape[0]), (shape[1], 0)]
    corners = [affine * p for p in corners]
    crn = transform(src_crs, dst_crs, [p[0] for p in corners],
                                      [p[1] for p in corners])

    y_pixel = abs(max(crn[1]) - min(crn[1])) / dst_shape[0]
    x_pixel = abs(max(crn[0]) - min(crn[0])) / dst_shape[1]
    dst_transform = (x_pixel, 0.0, min(crn[0]),
                     0.0, -y_pixel, max(crn[1]))

    return dst_transform


# ported from https://github.com/mapbox/geojson-area/blob/master/index.js
# returns area in square meters
def ringArea(coords):
    a = 0

    if len(coords) > 2:
        p1 = None
        p2 = None

        for i in range(0, len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i + 1]
            a += radians(p2[0] - p1[0]) * (2 + sin(radians(p1[1])) +
                                           sin(radians(p2[1])))

        a = a * wgs_r2 / 2

    return fabs(a)


def process(out, f, scale):
    with rasterio.open(f) as src:
        band = src.read(1)
        shape = src.shape
        crs = src.crs
        affine = src.affine
        meta = src.meta

    if (crs['init'] != 'epsg:4326'):
        dst_transform = dst_affine(affine, crs, shape)
        reproject(band, new_band, src_transform=affine, src_crs=crs,
                  dst_transform=dst_transform, dst_crs=dst_crs,
                  resampling=RESAMPLING.nearest)
        band = new_band
    else:
        dst_transform = affine

    lat = None
    new_band = np.zeros_like(band)
    for y in range(0, shape[0]):
        corners = [(0, y),
                   (1, y),
                   (1, y + 1),
                   (0, y + 1),
                   (0, y)]
        corners = [affine * p for p in corners]
        area = ringArea(corners)
        new_band[y, :] = band[y, :] * (area / 10000.0)

    new_band = ma.masked_array(new_band, mask=(band == meta['nodata']))
    new_band = new_band.filled(meta['nodata']).astype(rasterio.float32)

    out = path.join(out, path.basename(f))
    with rasterio.open(out,
                       mode='w', driver='GTiff',
                       width=shape[1],
                       height=shape[0],
                       count=1,
                       dtype=rasterio.float32,
                       nodata=meta['nodata'],
                       transform=dst_transform,
                       crs=dst_crs) as dst:
        dst.write_band(1, new_band)


parser = argparse.ArgumentParser()
parser.add_argument('--output', '-o', required=True)
parser.add_argument('--scale', '-s', default=10000, type=float)
parser.add_argument('files', metavar='FILE', type=str, nargs='+')
argv = parser.parse_args()

for f in argv.files:
    process(argv.output, f, argv.scale)
