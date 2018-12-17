# coding=utf-8

from __future__ import print_function
from builtins import zip
from builtins import range
import os
import sys
import shutil
import pyproj
import datetime
import time
import numpy
import re


def create_dirs(dirs, discard=False):
    '''helper function: create folder structure'''
    for p in dirs:
        if p.find("in_memory") != -1:
            continue
        if discard:
            print("Removing ", os.path.abspath(p))
            shutil.rmtree(p, ignore_errors=True)
        if not os.path.exists(p):
            os.makedirs(p)
    pass


def relocate(old_path, new_folder, new_ext=None):
    """relocate file at ```old_path``` to ```new_folder``` and change its extension to ```new_ext```

    Parameters
    -----------------
    old_path: string
        old file path

    new_folder: string
        the folder new file will be stored

    new_ext: string
        the extension of new file will be replaced by ````new_ext````
    """
    rootname, ext = os.path.splitext(os.path.basename(old_path))
    rootname = rootname.replace(".", "_").replace(" ", "_").replace("-", "_")
    base = os.path.basename(old_path)
    if new_ext is None:
        return os.path.join(new_folder, rootname + ext)
    if new_ext is "":
        return os.path.join(new_folder, rootname)
    else:
        # Add a "." in case forgotten
        return os.path.join(new_folder, rootname + (new_ext if new_ext.startswith(".") else ".%s" % new_ext))


def list_folder_sorted_ext(folder=".", ext=None):
    return sorted([p for p in os.listdir(folder) if ext is None or p.endswith(ext)])


def smart_lookup_date(dstring, dformat, try_again=False):
    a = re.compile(r"[-_\s:\.]")
    # Let us trim string first.
    dstring = a.sub("", dstring)
    dformat = a.sub("", dformat)
    dformat_len = len(datetime.datetime.strftime(datetime.datetime.now(), dformat))
    # print("date string length is", dformat_len)
    for i in range(len(dstring)):
        # End of search
        if i + dformat_len > len(dstring):
            break
        sub_dstring = dstring[i:i + dformat_len]
        try:
            p_datetime = datetime.datetime.strptime(sub_dstring, dformat)
        except ValueError:
            continue
        assert(isinstance(p_datetime, datetime.datetime))
        if 1950 < p_datetime.year < 2050:  # 100 year range should be long enough
            print(("Found datetime", p_datetime))
            return p_datetime
    if try_again:
        return None
    # We didn't find a datetime at all!
    # Well let us try if we can use a shorter one without seconds
    else:
        return smart_lookup_date(dstring, dformat.replace("%S", ""), True)


def __find_files_in_list_by_time(files, ref_time, dformat, mask_config=None, allow_diff_sec=300):
    if not files:
        return None, None
    r = time.mktime(ref_time.timetuple())
    # We need to be smart enough to find file name
    t = [smart_lookup_date(os.path.basename(os.path.splitext(f)[0]), dformat) for f in files]
    s = numpy.array([time.mktime(p.timetuple()) for p in t])
    d = numpy.abs(s - r)
    if numpy.min(d) > allow_diff_sec:
        return None, None
    i = numpy.argmin(d)
    mask = None
    if mask_config is not None:
        for m in mask_config:
            if m[0] <= t[i] < m[1]:
                mask = m[2]
                break
    return mask, files[i]


def list_files_by_timestamp(basedir, timelist, dformat, file_ext=None, mask_config=None, allow_diff_sec=300):
    '''find a list of files closest to given timelist'''
    files = list_folder_sorted_ext(basedir, file_ext)
    return list(zip(*[__find_files_in_list_by_time(files, t, dformat) for t in timelist]))


# default configs
#case_year = "2004"
#case_name = "Jeanne"

#central_meridian = -96.0
#standard_parallel_1 = 20.0
#standard_parallel_2 = 60.0
#latitude_of_origin = 40.0

#temp_folder = os.environ.get("TEMP", "/tmp")
#ibtrac = os.path.join(sys.path[0], 'ibtracs_na_1995.csv')
#cnt_folder = "cnt"
#cnt_polygon_folder = "cnt_polygon"
#stage1_folder = "basic_metric"
#stage2_folder = "adv_metric"
#projStr = "+proj=lcc +lat_1=%f +lat_2=%f +lat_0=%f +lon_0=%f +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs" % (
    #standard_parallel_1, standard_parallel_2, latitude_of_origin, central_meridian)
#projFunc = pyproj.Proj(projStr)
#spatialRef = ('PROJCS["North_America_Lambert_Conformal_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],' +
              #'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],' +
              #'PARAMETER["Central_Meridian",%f],PARAMETER["Standard_Parallel_1",%f],PARAMETER["Standard_Parallel_2",%f],PARAMETER["Latitude_Of_Origin",%f],UNIT["Meter",1.0],' +
              #'AUTHORITY["ESRI",102009]]') % (central_meridian, standard_parallel_1, standard_parallel_2, latitude_of_origin)

config_path = os.path.join(os.path.dirname(__file__), sys.argv[1].lower()) + ".py"
print("loading config from %s" % config_path)
block = compile(open(config_path).read(), __name__, mode='exec')
exec(block, globals(), locals())


