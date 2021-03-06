from __future__ import division
from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
import os

import arcpy
import numpy
import math

proj_template = 'PROJCS["North_Pole_Azimuthal_Equidistant",' \
                'GEOGCS["GCS_WGS_1984",' \
                'DATUM["D_WGS_1984",' \
                'SPHEROID["WGS_1984",6378137.0,298.257223563]],' \
                'PRIMEM["Greenwich",0.0],' \
                'UNIT["Degree",0.0174532925199433]],' \
                'PROJECTION["Azimuthal_Equidistant"],' \
                'PARAMETER["False_Easting",0.0],' \
                'PARAMETER["False_Northing",0.0],' \
                'PARAMETER["Central_Meridian",%f],' \
                'PARAMETER["Latitude_Of_Origin",%f],' \
                'UNIT["Meter",1.0],' \
                'AUTHORITY["Esri",102016]]'


class RadiantLine(object):

    def __init__(self, lon, lat, r_start=0, r_end=600, resolution=1, direction=0):
        self.r_start = r_start * 1000.0  # km -> m
        self.r_end = r_end * 1000.0
        self.proj = proj_template % (lon, lat)
        self.resolution = int(resolution)
        self.direction = direction

    def __enter__(self):
        self.__calculate_geometry()
        return self

    def __calculate_geometry(self):
        temp_name = arcpy.CreateScratchName("RadiantLine_%d" % os.getpid(), workspace="in_memory")
        arcpy.CreateFeatureclass_management(os.path.dirname(temp_name), os.path.basename(temp_name), "POLYLINE", spatial_reference=self.proj)
        arcpy.AddField_management(temp_name, "DEG", "TEXT")
        arcpy.AddField_management(temp_name, "QUAD", "TEXT")
        arcpy.AddField_management(temp_name, "MOVE", "TEXT")
        arcpy.AddField_management(temp_name, "MV_DEG", "TEXT")
        with arcpy.da.InsertCursor(temp_name, ["SHAPE@", "DEG", "QUAD", "MOVE", "MV_DEG"]) as cur:
            for i in range(0, 360, self.resolution):
                a = math.radians(i)
                start_x = self.r_start * math.cos(a)
                start_y = self.r_start * math.sin(a)
                end_x = self.r_end * math.cos(a)
                end_y = self.r_end * math.sin(a)
                line = arcpy.Polyline(arcpy.Array([arcpy.Point(start_x, start_y), arcpy.Point(end_x, end_y)]))
                cur.insertRow([line, str(i), str(int(old_div(i, 90)) + 1), str(int(old_div((i - self.direction) % 360, 90) + 1)), str(int((i - self.direction) % 360))])
        self.temp_name = temp_name

    def __exit__(self, exc_type, exc_val, exc_tb):
        if arcpy.Exists(self.temp_name):
            arcpy.Delete_management(self.temp_name)

    def copy(self, output_name):
        arcpy.Copy_management(self.temp_name, output_name)


if __name__ == "__main__":
    arcpy.env.overwriteOutput = True
    RadiantLine(lon=-84.3242, lat=33.9829, r_start=200, r_end=350).save(r"C:\Users\miaoji\Documents\ArcGIS\test.shp")
