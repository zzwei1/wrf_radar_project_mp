# This must be set here!
mode = "radar"
#mode = "wrf"


# radar configuration, not used in WRF mode
start_time_string = '2007-09-12 18:00:00'
end_time_string = '2007-09-14 11:55:00'
freq_string = "10min"

# configs
case_year = "2007"
case_name = "Humberto"

central_meridian = -96.0
standard_parallel_1 = 20.0
standard_parallel_2 = 60.0
latitude_of_origin = 40.0

temp_folder = os.environ.get("TEMP", "/tmp")
ibtrac = os.path.join(os.path.dirname(__file__), 'ibtracs_na_1995.csv')
cnt_folder = "cnt"
cnt_polygon_folder = "cnt_polygon"
stage1_folder = "basic_metric"
stage2_folder = "adv_metric"
projStr = "+proj=lcc +lat_1=%f +lat_2=%f +lat_0=%f +lon_0=%f +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs" % (
    standard_parallel_1, standard_parallel_2, latitude_of_origin, central_meridian)
projFunc = pyproj.Proj(projStr)
spatialRef = ('PROJCS["North_America_Lambert_Conformal_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],' +
              'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],' +
              'PARAMETER["Central_Meridian",%f],PARAMETER["Standard_Parallel_1",%f],PARAMETER["Standard_Parallel_2",%f],PARAMETER["Latitude_Of_Origin",%f],UNIT["Meter",1.0],' +
              'AUTHORITY["ESRI",102009]]') % (central_meridian, standard_parallel_1, standard_parallel_2, latitude_of_origin)

# Running config
radar_base_folder = r'/home/miaoji/Documents/H07'
wrf_base_folder = 'D:/isabel_wrf_restart/windfield'
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

search_radius = 500e3

# This is used for WRF only.
resolution = 30000
