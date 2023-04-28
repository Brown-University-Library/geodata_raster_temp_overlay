# -*- coding: utf-8 -*-
"""
Take a vector polygon file, calculate its bounding box, and use the box
to clip all temperature rasters in a folder, saving them as a new GeoTiff.
Also exports the bounding box out as a shapefile.

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
raster_path=os.path.join('input_raster','to_clip')
out_folder=os.path.join('input_raster','clipped')

clip_area = gpd.read_file(clip_file)

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

idx=0
for rf in os.listdir(raster_path):
    if rf.endswith('.bil'):
        raster_file=os.path.join(raster_path,rf)
        in_raster=rasterio.open(raster_file)
        # Do the clip operation
        out_raster, out_transform = mask(in_raster, areabbox.geometry, filled=False, crop=True)
        # Copy the metadata from the source and update the new clipped layer 
        out_meta=in_raster.meta.copy() 
        out_meta.update({
            "driver":"GTiff",
            "height":out_raster.shape[1], # height starts with shape[1]
            "width":out_raster.shape[2], # width starts with shape[2]
            "transform":out_transform})  
        # Write output to file
        out_file=rf.split('.')[0]+'.tif'
        out_path=os.path.join(out_folder,'clipped_'+out_file)
        with rasterio.open(out_path,'w',**out_meta) as dest:
            dest.write(out_raster)
        idx=idx+1
        if idx % 20 ==0:
            print('Processed',idx,'rasters so far...')
    else:
        pass
    
print('Finished clipping',idx,'raster files to bounding box: \n',corners)

#Show last clipped raster
fig, ax = plt.subplots(figsize=(12,12))
areabbox.plot(ax=ax, facecolor='none', edgecolor='black', lw=1.0)
show(in_raster,ax=ax)

fig, ax = plt.subplots(figsize=(12,12))
show(out_raster,ax=ax)

# Write bbox to shapefile 
areabbox.to_file(box_file)