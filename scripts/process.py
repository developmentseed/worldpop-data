import os
import re
import errno
import urllib
import argparse
import traceback
from tempfile import mkstemp
from urlparse import urlparse
import numpy as np
import numpy.ma as ma
import rasterio
from math import sin, fabs, radians
import boto3
import gzip
import shutil

# ============================================================
# PPP to PPH
# ============================================================

wgs_r2 = 6378137 * 6378137
dst_crs = {'init': 'epsg:4326'}


def dest_affine(affine, src_crs, shape):
    from rasterio.warp import transform
    corners = [(0, 0), (0, shape[0]), (shape[1], shape[0]), (shape[1], 0)]
    corners = [affine * p for p in corners]
    crn = transform(src_crs, dst_crs, [p[0] for p in corners],
                                      [p[1] for p in corners])

    y_pixel = abs(max(crn[1]) - min(crn[1])) / shape[0]
    x_pixel = abs(max(crn[0]) - min(crn[0])) / shape[1]
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


def ppp_to_pph(f, scale):
    from rasterio.warp import reproject
    print('ppp to pph', f)
    with rasterio.open(f) as src:
        band = src.read(1)
        shape = src.shape
        crs = src.crs
        affine = src.affine
        meta = src.meta

    unknown_crs = not (crs and 'init' in crs)
    if unknown_crs:
        print('Warning: unknown crs for '+f+'; assuming 4326')

    if (not unknown_crs and crs['init'] != 'epsg:4326'):
        dst_transform = dest_affine(affine, crs, shape)
        new_band = np.zeros_like(band)
        reproject(band, new_band, src_transform=affine, src_crs=crs,
                  dst_transform=dst_transform, dst_crs=dst_crs)
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

    return dict(band=new_band,
                meta=meta,
                affine=dst_transform)


def normalize(job):
    print('normalize', job)
    image_uri = job['image_uri']
    if not re.match('pph', image_uri):
        image_uri = download_and_unzip(image_uri)
        job.update(ppp_to_pph(image_uri, 10000))
        os.remove(image_uri)

    print('normalized', job)
    return job


# ============================================================
# POLYGONIZE
# ============================================================


def polygonize(dst_filename, dst_layername, dst_fieldname, src_filename):
    try:
        from osgeo import gdal, ogr, osr
    except ImportError:
        import gdal
        import ogr
        import osr

    print('polygonize', src_filename, dst_filename)
    src_ds = gdal.Open(src_filename)
    if src_ds is None:
        raise Exception('Unable to open %s' % src_filename)

    maskband = None

    srs = None
    if src_ds.GetProjectionRef() != '':
        srs = osr.SpatialReference()
        srs.ImportFromWkt(src_ds.GetProjectionRef())

    drv = ogr.GetDriverByName('GeoJSON')
    dst_ds = drv.CreateDataSource(dst_filename)

    dst_layer = dst_ds.CreateLayer(dst_layername, srs=srs)
    fd = ogr.FieldDefn(dst_fieldname, ogr.OFTInteger)
    dst_layer.CreateField(fd)
    dst_field = 0

    srcband = src_ds.GetRasterBand(1)
    prog_func = gdal.TermProgress

    options = []
    return gdal.Polygonize(srcband, maskband, dst_layer, dst_field, options,
                           callback=prog_func)

APP_NAME = 'worldpop-polygonize'


def get_filename(uri):
    name = os.path.splitext(os.path.basename(uri))[0]
    if not re.match('[A-Z]{3}', name):
        name = re.search('[A-Z]{3}', uri).group(0) + name
    return name


def mkdir_p(dir):
    try:
        os.makedirs(dir)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dir):
            pass
        else:
            raise


def download_and_unzip(uri):
    """
    Downloads and, if necessary, unzips the given uri.  Returns the path
    to the downloaded tempfile, which the using code should take care of
    deleting.
    """
    parsed = urlparse(uri)
    gzipped = uri.endswith('.gz')
    result_path = ""
    if not parsed.scheme:
        result_path = uri
        if not gzipped:
            (_, filecopy) = os.path.basename(result_path)
            with open(result_path, 'rb') as fin, \
                    open(filecopy, 'wb') as fout:
                shutil.copyfileobj(fin, fout)
            os.remove(result_path)
            return filecopy
    else:
        suffix = os.path.basename(parsed.path)
        (_, tmp) = mkstemp(suffix=suffix[suffix.index('.'):])
        if parsed.scheme == "s3":
            client = boto3.client("s3")
            bucket = parsed.netloc
            key = parsed.path[1:]
            client.download_file(bucket, key, tmp)
        elif parsed.scheme == "http":
            urllib.retrieve(uri, tmp)
        else:
            raise Exception("Unsupported scheme: %s" % parsed.scheme)

        result_path = tmp

    if gzipped:
        suffix = os.path.basename(result_path)
        suffix = suffix[suffix.index('.'):-3]
        (_, unzipped) = mkstemp(suffix=suffix)
        with gzip.open(result_path, 'rb') as z, \
                open(unzipped, 'wb') as uz:
            shutil.copyfileobj(z, uz)
        os.remove(result_path)
        result_path = unzipped

    return result_path


def write_bytes_to_target(target_uri, contents):
    parsed_target = urlparse(target_uri)
    if parsed_target.scheme == "s3":
        client = boto3.client("s3")

        bucket = parsed_target.netloc
        key = parsed_target.path[1:]

        print('putting ' + target_uri)
        response = client.put_object(
            ACL="public-read",
            Body=bytes(contents),
            Bucket=bucket,
            # CacheControl="TODO",
            ContentType="image/tiff",
            Key=key
        )
    else:
        output_path = target_uri
        mkdir_p(os.path.dirname(output_path))

        with open(output_path, "w") as f:
            f.write(contents)


def make_polygons(job):
    basename = get_filename(job['image_uri'])
    dest_uri = os.path.join(job['output'], basename + '.geojson')

    if 'band' in job:
        (_, tmp_tiff) = mkstemp(suffix='.tif', prefix=basename)
        with rasterio.open(tmp_tiff,
                           mode='w', driver='GTiff',
                           width=job['band'].shape[1],
                           height=job['band'].shape[0],
                           count=1,
                           dtype=rasterio.float32,
                           nodata=job['meta']['nodata'],
                           transform=job['affine'],
                           crs=dst_crs) as dst:
            dst.write_band(1, job['band'])
        image_file = tmp_tiff
    else:
        image_file = download_and_unzip(job['image_uri'])

    tmp_geojson = tmp_tiff.replace('tif', 'geojson')
    polygonize(tmp_geojson, 'population', 'density_pph', image_file)
    with open(tmp_geojson, 'rb') as f_in, \
            gzip.open(tmp_geojson + '.gz', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    with open(tmp_geojson + '.gz', 'rb') as f:
        write_bytes_to_target(dest_uri, f.read())
    os.remove(image_file)
    os.remove(tmp_geojson)
    os.remove(tmp_geojson + '.gz')


def run_jobs(request):
    print('Running with arguments:', request)

    # modify this to suit your argument data
    data = request.data
    output = request.output

    for im in data:
        try:
            job = dict(image_uri=im, output=output)
            make_polygons(normalize(job))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            err = traceback.format_exc()
            print('Error processing: ' + im)
            print('\t' + err.replace('\n', '\n\t'))

    print "Done."

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', required=True)
    parser.add_argument('data', metavar='FILE', type=str, nargs='+')
    args = parser.parse_args()
    run_jobs(args)
