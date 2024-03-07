# -*- coding: utf-8 -*-
"""
This is an basic, early version of temp_overlay_iterate.py that takes
point observations stored in a vector file, overlays them on a temperature
raster, and obtains the temperature. Does NOT account for observation dates
in input file.

Assumes points and rasters share the same coordinate system (NAD 83).

PRISM Climate Data: https://www.prism.oregonstate.edu/

Frank Donnelly / GIS and Data Librarian / Brown University
April 19, 2023 / revised March 4, 2024
"""
import os
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
from rasterio.plot import show

point_file=os.path.join('input_points','test_obsv.shp')
raster_file=os.path.join('input_raster','clipped','clipped_PRISM_tmean_stable_4kmD2_20200101_bil.tif')

#open point shapefile
point_data = gpd.read_file(point_file)
print(point_data.crs)
point_data.plot()

raster = rasterio.open(raster_file)
print(raster.crs)
print(raster.count)

fig, ax = plt.subplots(figsize=(12,12))
point_data.plot(ax=ax, color='black')
show(raster, ax=ax)

#extract xy from point geometry
for point in point_data['geometry']:
    print(point.x,point.y)

#extract point value from raster
for point in point_data['geometry']:
    x = point.x
    y = point.y
    row, col = raster.index(x,y)
    print("Point correspond to row, col: %d, %d"%(row,col))
    if any ([row < 0, row > raster.height, col < 0, col > raster.width]):
        print("Out of bounds at %d, %d \n"%(row,col))
    else:
        print("Raster value on point %.2f \n"%raster.read(1)[row,col])
    
point_data['temp']=raster.read(1)[raster.index(point_data['geometry'].x,point_data['geometry'].y)]

print(point_data)