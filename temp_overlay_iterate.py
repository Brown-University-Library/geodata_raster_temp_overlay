# -*- coding: utf-8 -*-
"""
Take the date from point observations stored in a vector file,
select the corresponding temperature raster for that date
and obtain the temperature. With option to pull temperatures for 
N days before that date and calculate average and range.

Assumes points and rasters share the same coordinate system (NAD 83)
and that rasters share the same resolution and extent.

PRISM Climate Data: https://www.prism.oregonstate.edu/

Frank Donnelly / GIS and Data Librarian / Brown University
April 19, 2023 / revised April 28, 2023
"""
import os,csv,rasterio
import matplotlib.pyplot as plt
import geopandas as gpd
from rasterio.plot import show
from datetime import datetime as dt
from datetime import timedelta
from datetime import date

#Calculate temps over multiple previous days from observation?
temp_many_days=True # True or False
date_range=(1,7) # Range of past dates 

#Inputs
point_file=os.path.join('input_points','test_obsv.shp')
raster_dir=os.path.join('input_raster','clipped')
outfolder='output'
if not os.path.exists(outfolder):
    os.makedirs(outfolder)

# Column names in point file that contain: unique ID, name, and date
obnum='OBS_NUM'
obname='OBS_NAME'
obdate='OBS_DATE'

rf_dict={} # Create dictionary of dates and raster file names

for rf in os.listdir(raster_dir):
    if rf.endswith('.tif'):
        rfdatestr=rf.split('_')[5]
        rfdate=dt.strptime(rfdatestr,'%Y%m%d').date() #format of dates is 20200131
        rfpath=os.path.join(raster_dir,rf)
        rf_dict[rfdate]=rfpath
    else:
        pass
    
#open point shapefile
point_data = gpd.read_file(point_file)

result_list=[]
result_list.append(['OBS_NUM','OBS_NAME','OBS_DATE','RASTER_ROW','RASTER_COL','RASTER_FILE','TEMP'])

if temp_many_days==True:
    for d in range(date_range[0],date_range[1]):
        tcol='TMINUS_'+str(d)
        result_list[0].append(tcol)
    result_list[0].append('TEMP_RANGE')
    result_list[0].append('AVG_TEMP')
    temp_ftype='multiday_'
else:
    temp_ftype='singleday_'

#Pull out and format the date, and use date to look up file
for idx in point_data.index:
    obs_date=dt.strptime(point_data[obdate][idx],'%m/%d/%Y').date() #format of dates is 1/31/2020
    obs_raster=rf_dict.get(obs_date)
    if obs_raster == None:
        print('No raster available for observation and date',
              point_data[obnum][idx],point_data[obdate][idx])
    #Open raster for matching date, overlay point coordinates, get cell location and value
    else:
        raster=rasterio.open(obs_raster)
        xcoord=point_data['geometry'][idx].x
        ycoord=point_data['geometry'][idx].y
        row, col = raster.index(xcoord,ycoord)
        tempval=raster.read(1)[row,col]
        rfile=os.path.split(obs_raster)[1]
        record=[point_data[obnum][idx],point_data[obname][idx],
                point_data[obdate][idx],row,col,rfile,tempval]
    # Optional block, if pulling past dates
        if temp_many_days==True:
            old_temps=[]
            for d in range(date_range[0],date_range[1]):
                past_date=obs_date-timedelta(days=d) # iterate through days, subtracting
                past_raster=rf_dict.get(past_date)
                if past_raster == None: # if no raster exists for that date
                    old_temps.append(None)
                else:
                    old_raster=rasterio.open(past_raster)
                    # Assumes rasters from previous dates are identical in structure to 1st date
                    past_temp=old_raster.read(1)[row,col]
                    old_temps.append(past_temp)
            # Calculate avg and range, must exclude None values and include obs day
            all_temps=[t for t in old_temps if t is not None]
            all_temps.append(tempval)
            temp_range=max(all_temps)-min(all_temps)
            avg_temp=sum(all_temps)/len(all_temps)
            old_temps.extend([temp_range,avg_temp])
            record.extend(old_temps)
            result_list.append(record)
        else: # if NOT doing many days, just append data for observation day
            result_list.append(record)
    if (idx+1)%200==0:
        print('Processed',idx+1,'records so far...')
            
#Plot the points over the final raster that was processed    
fig, ax = plt.subplots(figsize=(12,12))
point_data.plot(ax=ax, color='black')
show(raster, ax=ax)

today=str(date.today()).replace('-','_')
outfile='temp_observations_'+temp_ftype+today+'.csv'
outpath=os.path.join(outfolder,outfile)

with open(outpath, 'w', newline='') as writefile:
    writer=csv.writer(writefile, quoting=csv.QUOTE_MINIMAL, delimiter=',')
    writer.writerows(result_list)  

print('Done. {} observations in input file, {} records in results'.format(len(point_data),len(result_list)-1))
    
    