# http://gis.stackexchange.com/questions/14712/splitting-raster-into-smaller-chunks-using-gdal
import os, sys
from osgeo import gdal

dset = gdal.Open(sys.argv[1])

width = dset.RasterXSize
height = dset.RasterYSize

print width, 'x', height

tilesize = 5000

for i in range(0, width, tilesize):
    for j in range(0, height, tilesize):
        w = min(i+tilesize, width) - i
        h = min(j+tilesize, height) - j
        gdaltranString = "gdal_translate -of GTIFF -srcwin "+str(i)+", "+str(j)+", "+str(w)+", " \
            +str(h)+" " + sys.argv[1] + " " + sys.argv[2] + "_"+str(i)+"_"+str(j)+".tif"
        os.system(gdaltranString)
