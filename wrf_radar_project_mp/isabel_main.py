import sys
import os
import datetime

import pandas as pd

import arcpy

import utils
import mp_start

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True
arcpy.env.workspace = "in_memory"

radar_base_folder = r'E:\radar_isabel'

# wrf_base_folder = r'C:\Users\sugar\Desktop\wrf3.6.1'
wrf_base_folder = r'D:\isabel_wrf_restart\windfield'

# Biased cases
wrf_schemes = [  
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

radar_levels = range(20, 45, 5)
wrf_bias = (
    # [23, 28, 33, 38, 44],  # KF/M
    # [14, 20, 27, 34, 41],  # KF/WSM6
    # [20, 25, 29, 34, 40],  # TK/M
    # [17, 23, 28, 33, 40],  # TK/WSM6
    # None,
    # None,
    # None,
    # None,
    # None,
    # None,
    # None
    [17, 33, 50],
    [17, 33, 50],
    [17, 33, 50]
)


def run_radar(skip_list, discard_existed):
    # Radar resolution = 30min, WRF resolution = 30min
    analytical_time = map(pd.Timestamp.to_datetime,
                          pd.date_range('2003-09-18 00:00:00', 
                                        '2003-09-18 01:00:00', 
                                        freq="30min"))
    print(analytical_time)
    utils.working_mode = "radar"
    _, file_list = utils.list_files_by_timestamp(radar_base_folder,
                                                 analytical_time,
                                                 allow_diff_sec=600,
                                                 file_ext="img",
                                                 dformat="%Y%m%d-%H%M%S")
    mp_start.start_mp(work_base_folder=radar_base_folder,
                      file_list=file_list,
                      levels=radar_levels,
                      working_mode="radar",
                      stage2_datetime_format="%Y%m%d_%H%M%S",
                      skip_list=skip_list,
                      discard=discard_existed)


def run_wrf(case, skip_list, discard_existed):
    # global masks
    utils.working_mode = "wrf"
    if wrf_bias[case]:
        wrf_levels = wrf_bias[case]
    else:
        wrf_levels = radar_levels

    mp_start.start_mp(work_base_folder=os.path.join(wrf_base_folder, wrf_schemes[case]),
                      file_list=None,
                      levels=wrf_levels,
                      masks=None,
                      working_mode="wrf",
                      stage2_datetime_format="V850_d01_850mb_%Y_%m_%d_%H_%M",
                      skip_list=skip_list,
                      discard=discard_existed)


def main(argv):
    discard_existed = True
    skip_dict = {
        "contour": 0,
        "smooth": 0,
        "basic": 0,
        "closure": 0,
    }
    skip_list = [k for k,v in skip_dict.iteritems() if v]
    
    # If we do the skip, we cannot discard previous results
    if skip_list:
        discard_existed = False
    print skip_list, discard_existed
    utils.skip_list = skip_list
    case = 0
    try:
        case = int(argv[1])
    except IndexError:
        pass
    if case < 0:
        run_radar(skip_list, discard_existed)
    else:
        run_wrf(case, skip_list, discard_existed)

    # Do change here!
    search_radius = 500e3
    try:
        search_radius = int(argv[2]) * 1000
    except (IndexError, ValueError):
        pass
    utils.search_radius = search_radius



if __name__ == "__main__":
    main(sys.argv)
