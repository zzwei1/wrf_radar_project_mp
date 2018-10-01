import sys
import os
import datetime

import pandas as pd
from pprint import pprint as pp

import arcpy

import utils
import mp_start

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True
arcpy.env.workspace = "in_memory"

radar_base_folder = r'D:\H07\3_5'

# wrf_base_folder = r'C:\Users\sugar\Desktop\wrf3.6.1'
wrf_base_folder = r'D:\isabel_wrf_restart\windfield'

wrf_schemes = [  # Biased cases
    # 'ARWH_KainFritschCu_Morrison', #0
    # 'ARWH_KainFritschCu_WSM6',
    # 'ARWH_TiedtkeCu_Morrison',
    # 'ARWH_TiedtkeCu_WSM6',
    # # Unbiased cases
    # 'ARWH_KainFritschCu_Morrison', #4
    # 'ARWH_KainFritschCu_WDM6',
    # 'ARWH_KainFritschCu_WSM6',
    # 'ARWH_TiedtkeCu_Morrison',
    # 'ARWH_TiedtkeCu_WDM6',
    # 'ARWH_TiedtkeCu_WSM6', #9
    # 'wrf_gary',
    # Wind cases
    'KFS',
    'TS',
    'zTS'
]
wrf_postfix = ''

# masks = [(datetime.datetime(2003, 9, 18, 0, 0, 0), datetime.datetime(2003, 9, 18, 23, 59, 59),
#          r'E:\wrf3.6.1\Mask\mask1.shp'),
#         (datetime.datetime(2003, 9, 19, 0, 0, 0), datetime.datetime(2003, 9, 19, 23, 59, 59),
#          r'E:\wrf3.6.1\Mask\mask2.shp')]

radar_levels = [20, 40]


def run_radar(skip_list, discard_existed):
    # Radar resolution = 30min, WRF resolution = 30min
    analytical_time = map(pd.Timestamp.to_datetime,
                          pd.date_range('2007-09-12 18:00:00', '2007-09-14 12:00:00', freq="10min"))
    utils.working_mode = "radar"
    print(analytical_time)
    _, file_list = utils.list_files_by_timestamp(radar_base_folder,
                                                 analytical_time,
                                                 allow_diff_sec=5,
                                                 file_ext="img",
                                                 dformat="%Y%m%d_%H%M%S")
    pp(file_list)
    mp_start.start_mp(work_base_folder=radar_base_folder,
                      file_list=file_list,
                      levels=radar_levels,
                      working_mode="radar",
                      stage2_datetime_format="%Y%m%d_%H%M%S",
                      skip_list=skip_list,
                      discard=discard_existed)


def run_wrf(case, skip_list, discard_existed):
    pass


def main(argv):
    discard_existed = True
    skip_dict = {
        "contour": 1,
        "smooth": 1,
        "basic": 1,
        "closure": 0,
    }
    skip_list = [k for k,v in skip_dict.iteritems() if v]
    # If we do the skip, we cannot discard previous results
    if skip_list:
        discard_existed = False
    print skip_list, discard_existed
    utils.skip_list = skip_list
    # So we run radar case
    case = -1
    try:
        case = int(argv[1])
    except IndexError:
        pass
    if case < 0:
        run_radar(skip_list, discard_existed)
    else:
        run_wrf(case, skip_list, discard_existed)

    search_radius = 500e3
    try:
        search_radius = int(argv[2]) * 1000
    except (IndexError, ValueError):
        pass
    utils.search_radius = search_radius


if __name__ == "__main__":
    main(sys.argv)
