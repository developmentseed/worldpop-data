#!/bin/sh -e

# Bootstrap an Amazon Linux machine to prepare it to run `process.py`, which takes
# worldpop tifs and polygonizes them to geojson

sudo yum-config-manager --enable epel
sudo yum -y install geos proj proj-nad proj-epsg
sudo ln -s /usr/lib64/libproj.so.0 /usr/lib64/libproj.so

# build GDAL from source
# curl http://download.osgeo.org/gdal/2.0.1/gdal-2.0.1.tar.gz | tar zxf -
# cd gdal-2.0.1/
# ./configure
# make
# make install

# or use the prebuilt one, which was built with the following steps:
# mkdir ~/gdal
# ./configure --prefix=$HOME/gdal
# make
# make install
# tar -czf gdal-2.0.1-aws-emr-4.0.0.tar.gz -C $HOME/gdal .
curl https://s3-us-west-2.amazonaws.com/world-pop/spark/gdal-2.0.1-aws-emr-4.0.0.tar.gz | sudo tar -zxf - -C /usr/local

# python libs (raterio installs numpy, so do this before the GDAL py bindings)
sudo GDAL_CONFIG=/usr/local/bin/gdal-config pip-2.7 install boto3 rasterio mercantile psutil

# GDAL python bindings
curl https://pypi.python.org/packages/source/G/GDAL/GDAL-2.0.1.tar.gz | tar zxf -
cd GDAL-2.0.1
curl https://s3-us-west-2.amazonaws.com/world-pop/spark/setup.cfg > setup.cfg
python2.7 setup.py build
sudo python2.7 setup.py install

# gnu parallel
# From http://software.opensuse.org/download.html?project=home%3Atange&package=parallel
cd /etc/yum.repos.d/
sudo wget http://download.opensuse.org/repositories/home:tange/RedHat_RHEL-6/home:tange.repo
sudo yum -y install parallel
cd

# permissions
sudo chmod 777 /mnt1

echo "export GDAL_DATA=/usr/local/share/gdal" > set_paths.sh
echo "export LD_LIBRARY_PATH=/usr/local/lib" >> set_paths.sh
echo "export TMPDIR=/mnt1" >> set_paths.sh

source set_paths.sh

echo "Ready to go!"

