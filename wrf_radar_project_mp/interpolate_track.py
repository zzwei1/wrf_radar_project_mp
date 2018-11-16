#coding=utf-8

from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import os
import csv
import pickle

import datetime
import time
from pprint import pprint as pp

import numpy
import math
from scipy.interpolate import interp1d
from scipy.misc import derivative

import pyproj

import utils



def date_to_timestamp(row):
    try:
        year = int(row['Year'])
        month = int(row['Month'])
        day = int(row['Day'])
        hour = int(row['Hour'])
        row_date = datetime.datetime(year, month, day, hour, 0, 0)
        return [time.mktime(row_date.timetuple()), float(row['Lon']), float(row['Lat'])]
    except: 
        return date_to_timestamp_ibtracs(row)


def date_to_timestamp_ibtracs(row):
    case_name = utils.case_name.upper()
    if row['Season'] != utils.case_year or row['Name'] != case_name:
        return None
    t_date, t_time = row['ISO_time'].split(' ')
    t_year, t_month, t_day = t_date.split('/')
    t_hour, t_ = t_time.split(':')
    return [time.mktime(datetime.datetime(int(t_year), int(t_month), int(t_day), int(t_hour), 0, 0).timetuple()), 
            float(row['Longitude_for_mapping']), float(row['Latitude_for_mapping'])]
    

def main(input_csv_path, work_base_folder, input_data_folder, date_format="%Y%m%d_%H%M%S", str_start=0, str_end=15):
    """Interpolate track from given csv file and pickle it to disk"""
    proj = pyproj.Proj(utils.projStr)
    csvfile = open(input_csv_path) 
    reader = csv.DictReader(csvfile)
    track_list = [p for p in [date_to_timestamp(row) for row in reader] if p is not None]
    csvfile.close()
    
    track_array = numpy.array(track_list)
    print(track_array)
    T = track_array[:,0]
    X = track_array[:,1]
    Y = track_array[:,2]
    
    fx = interp1d(T, X, kind='cubic')
    fy = interp1d(T, Y, kind='cubic')

    # List files
    date_str = utils.list_folder_sorted_ext(input_data_folder, ".img")
    date_obj = [utils.smart_lookup_date(p, date_format) for p in date_str]
    timestamps = [time.mktime(p.timetuple()) for p in date_obj]
    interp_track_dict = {}
    for i in range(len(timestamps)):
        p = timestamps[i]
        pp(date_str[i])
        try:
            interp_track_dict[p] = {}
            interp_track_dict[p]['pos'] = proj(fx(p), fy(p))
            vx = derivative(fx, p)
            vy = derivative(fy, p)
            interp_track_dict[p]['dir'] = int(math.degrees(math.atan2(vy, vx)))
        except:
            pp("ERROR")
    pp(interp_track_dict)
    
    with open(os.path.join(work_base_folder, utils.case_name + ".pickle"), "wb") as track_dump:
        pickle.dump(interp_track_dict, track_dump)
        
            
if __name__ == "__main__":
    main(utils.ibtrac, utils.radar_base_folder, utils.radar_base_folder, "%Y%m%d_%H%M%S")
        
    
    
    
    
    