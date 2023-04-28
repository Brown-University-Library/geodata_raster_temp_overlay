# -*- coding: utf-8 -*-
"""
This is an early, basic version of temp_clipper_batch.py that clips a single file.
Take a vector polygon file, calculate its bounding box, and use the box
to clip one temperature raster, saving it as GeoTiff.

Assumes polygons and rasters share the same coordinate system (NAD 83).

PRISM Climate Data: https://www.prism.oregonstate.edu/

Frank Donnelly / GIS and Data Librarian / Brown University
April 19, 2023
"""
import os
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import Polygon
from rasterio.plot import show
# from datetime import datetime as dt

#Inputs
clip_file=os.path.join('input_raster','mask','states_southern_ne.shp')
# new file created by script:
box_file=os.path.join('input_raster','mask','states_southern_ne_bbox.shp') 
raster_file='PRISM_tmean_stable_4kmD2_20200101_bil.bil'
raster_path=os.path.join('input_raster','to_clip',raster_file)
out_folder=os.path.join('input_raster','clipped')

clip_area = gpd.read_file(clip_file)
print("Clip file CRS: \n",clip_area.crs)
raster=rasterio.open(raster_path)
print("Input raster CRS: \n",raster.crs)

# Calculate bounding box for entire clip layer, and create geodataframe
corners=clip_area.total_bounds
minx=corners[0]
miny=corners[1]
maxx=corners[2]
maxy=corners[3]
areabbox = gpd.GeoDataFrame({'geometry':Polygon([(minx,maxy),
                                                (maxx,maxy),
                                                (maxx,miny),
                                                (minx,miny),
                                                (minx,maxy)])},index=[0],crs="EPSG:4269")

# Do the clip operation
out_raster, out_transform = mask(raster, areabbox.geometry, filled=False, crop=True)

# Copy the metadata from the source and update the new clipped layer 
out_meta=raster.meta.copy() 
out_meta.update({
    "driver":"GTiff",
    "height":out_raster.shape[1], # height starts with shape[1]
    "width":out_raster.shape[2], # width starts with shape[2]
    "transform":out_transform
})

print("Output raster CRS: \n",out_meta['crs'])

fig, ax = plt.subplots(figsize=(12,12))
show(out_raster,ax=ax)

# Write output to file
out_file=raster_file.split('.')[0]+'.tif'
out_path=os.path.join(out_folder,'clipped_'+out_file)

with rasterio.open(out_path,'w',**out_meta) as dst:
    out_path=os.path.join(out_folder,out_file)
    dst.write(out_raster)
    
areabbox.to_file(box_file)