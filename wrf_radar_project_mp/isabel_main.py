from __future__ import print_function
from builtins import map
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

radar_base_folder = utils.radar_base_folder
wrf_base_folder = utils.wrf_base_folder
wrf_schemes = utils.wrf_schemes
wrf_postfix = utils.wrf_postfix
# masks = utils.masks
radar_levels = utils.radar_levels


def run_radar(skip_list, discard_existed):
    # Radar resolution = 30min, WRF resolution = 30min
    analytical_time = list(map(pd.to_datetime, pd.date_range(utils.start_time_string, utils.end_time_string, freq=utils.freq_string)))
    utils.working_mode = "radar"
    pp(analytical_time)
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
        "contour": 1,
        "smooth": 1,
        "basic": 1,
        "adv": 0,
        "closure": 0,
    }

    skip_list = [k for k,v in list(skip_dict.items()) if v]
    # If we do the skip, we cannot discard previous results
    if skip_list:
        discard_existed = False
    print(skip_list, discard_existed)
    utils.skip_list = skip_list
    # So we run radar case
    case = 0
    if utils.mode == 'radar':
        print("Running in radar mode, case number is not used at all")
        run_radar(skip_list, discard_existed)
        case = -1
    else:
        try:
            case = int(argv[2])
            if case < 0:
                raise ValueError("Case number must >= 0")
            run_wrf(case, skip_list, discard_existed)
        except Exception as e:
            print("You must provide a valid case number in WRF mode")
            

if __name__ == "__main__":
    main(sys.argv)
