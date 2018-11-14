# coding=utf-8


from __future__ import division
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from past.utils import old_div
import os
import datetime
import time
import pickle
import math
import sys
import logging

import pyproj
import utils
from add_basic_geometry import calc_field
from create_radiant_line import RadiantLine

import numpy

import arcpy
import arcpy.da

from add_basic_geometry import add_basic_geometry_attr

from pprint import pprint

# def calc_closure(geom, x0, y0):
#     parts = geom.getPart()
#     closure = {}
#     for part in parts:
#         rad = numpy.array([math.atan2(y0 - point.Y, x0 - point.X) for point in part if point is not None])
#         rad[rad < 0] += 2 * numpy.pi
#         deg = ((rad * 180.0 / numpy.pi).astype('int32')).tolist()
#         closure.update(dict(zip(deg, [True] * len(deg))))
#     return closure

g = pyproj.Geod(utils.projStr)


def line_dist(pt1, pt2):
    lon1, lat1 = utils.projFunc(pt1[0], pt1[1], inverse=True)
    lon2, lat2 = utils.projFunc(pt2[0], pt2[1], inverse=True)
    _, _, s = g.inv(lon1, lat1, lon2, lat2)
    a = math.degrees(math.atan2(pt2[1] - pt1[1], pt2[0] - pt1[0]))
    return s, a


def generate_dispersiveness(polygon, levels, workspace="in_memory", move_dir=0):
    arcpy.env.workspace = "in_memory"
    dispersiveness = ""
    closure_str = ""
    fragmentation = ""
    roundness = ""
    adv_elongation = ""
    displacements_e = ""
    displacements_n = ""
    extent_str = ""
    extent_mv_str = ""
    large_str = ""
    large_attr_list = []
    dispersive_search_radius = (100e3, 150e3, 200e3, 250e3, 500e3)

    for l in levels:

        # list for dispersiveness
        l_dispersive = []
        # list for fragmentation
        l_frag = []
        # list for roundness
        l_round = []
        # list to collect areas
        _areas_list = []
        # dict for closure
        # closure = dict(zip(range(360), [False]*360))
        # list for displacement
        l_displace = []

        eye_x = 0
        eye_y = 0

        # We need multiple level radar
        for lr in dispersive_search_radius:
            with arcpy.da.SearchCursor(polygon,
                                       ["AREA", "TO_EYE", "SHAPE@", "EYE_X", "EYE_Y", "AREA_CVX", "PERIM", "SUM_AREA", "ANGLE"],
                                       where_clause="dBZ=%d and TO_EYE<=%f" % (l, lr)) as cur:
                l_dispersive = []
                cur.reset()
                for row in cur:
                    # Dispersiveness
                    l_dispersive.append([row[0], row[1]])
                # Calculate dispersiveness
                areas = numpy.array(l_dispersive)
                if areas.shape != (0,):
                    total_areas = numpy.sum(areas[:, 0])
                    area_frac = old_div(areas[:, 0], total_areas)
                    dist_weight = old_div(areas[:, 1], lr)
                    dispersiveness += "%f|" % numpy.sum(area_frac * dist_weight)
                else:
                    dispersiveness += "|"
        if dispersiveness.endswith("|"):
            dispersiveness = dispersiveness[:-1]
        dispersiveness += ","

        with arcpy.da.SearchCursor(polygon,
                                   ["AREA", "TO_EYE", "SHAPE@", "EYE_X", "EYE_Y", "AREA_CVX", "PERIM", "SUM_AREA", "ANGLE"],
                                   where_clause="dBZ=%d" % (l,)) as cur:
            cur.reset()
            for row in cur:
                # # For closure, we need exclude polygon in 50km buffer closed to the eye
                # if row[1] >= 50000:
                #     geom, x0, y0 = row[2:5]
                #     cl = calc_closure(geom, x0, y0)
                #     closure.update(cl)
                # Fragment
                l_frag.append((row[0], row[5]))
                # Roundness
                l_round.append((row[0], row[6], row[7]))
                # Area list
                # _areas_list.append(row[0])
                # displacement
                l_displace.append((row[0], row[1], row[8]))
                # we need eye_x, eye_y for closure center
                eye_x = row[3]
                eye_y = row[4]

        # Calculate fragmentation.
        fareas = numpy.array(l_frag)
        if fareas.shape != (0,):
            total_areas = numpy.sum(fareas[:, 0])
            total_cvx_areas = numpy.sum(fareas[:, 1])
            solidity = old_div(total_areas, total_cvx_areas)
            # Connectivity
            sareas = fareas.shape[0]
            conn = 1 - (old_div((sareas - 1), ((old_div(total_areas, 9)) ** 0.5 + sareas)))
            fragmentation += "%f," % (1 - solidity * conn)
        else:
            fragmentation += ","

        # Asymmetry/Roundness
        # I think, it should be OK for each polygon, but I think it hurt nothing to calculate it here.
        rareas = numpy.array(l_round)
        if fareas.shape != (0,):
            max_rareas = rareas[numpy.argmax(rareas, 0)]
            # R = base_roundness * size_factor
            R = numpy.mean(old_div(4 * max_rareas[:, 0] * math.pi, numpy.square(max_rareas[:, 1]) * (
                    old_div(numpy.log(max_rareas[:, 0]), numpy.log(max_rareas[:, 2])))))
            roundness += "%f," % (1 - R)
        else:
            roundness += ","

        # Calculate displacement
        areas = numpy.array(l_displace)
        if areas.shape != (0,):
            total_areas = numpy.sum(areas[:, 0])
            area_frac = old_div(areas[:, 0], total_areas)
            dist_weight_e = areas[:, 1] * numpy.sin(numpy.radians(areas[:, 2])) / 1000.0  # Let's scale it to km, otherwise it will be too large
            dist_weight_n = areas[:, 1] * numpy.cos(numpy.radians(areas[:, 2])) / 1000.0
            displacements_e += "%f," % numpy.sum(area_frac * dist_weight_e)
            displacements_n += "%f," % numpy.sum(area_frac * dist_weight_n)
        else:
            displacements_e += ","
            displacements_n += ","

        pid = os.getpid()

        # Now we we can do closure in old way
        if "closure" not in utils.skip_list:
            closure_ring_km = [(0, 100), (100, 200), (200, 300), (300, 400), (400, 500), (0, 500)]
            select3 = arcpy.Select_analysis(polygon, "in_memory/select_temp_3_%d" % pid, where_clause="dBZ=%d" % l)
            eye_lon, eye_lat = utils.projFunc(eye_x, eye_y, inverse=True)
            for s, e in closure_ring_km:
                with RadiantLine(lon=eye_lon, lat=eye_lat, r_start=s, r_end=e) as radiant:
                    arcpy.Intersect_analysis(in_features=["in_memory/select_temp_3_%d" % pid, radiant.temp_name],
                                             out_feature_class="in_memory/closure_temp_%d" % pid, join_attributes="ALL", output_type="INPUT")
                    with arcpy.da.SearchCursor("in_memory/closure_temp_%d" % pid, ["SHAPE@", "DEG"]) as q:
                        count = set()
                        for k in q:
                            count.add(k[1])
                        closure_str += "%.2f|" % (len(count) / 360.0)
                # arcpy.Delete_management("in_memory/select_temp.shp")
                # arcpy.Delete_management("in_memory/closure_temp.shp")
            # Remove last "|"
            if closure_str.endswith("|"):
                closure_str = closure_str[:-1]
            closure_str += ","

        if "extent" not in utils.skip_list:
            select4 = arcpy.Select_analysis(polygon, "in_memory/select_temp_4_%d" % pid, where_clause="dBZ=%d" % l)
            eye_lon, eye_lat = utils.projFunc(eye_x, eye_y, inverse=True)
            extent_mv = {"1": [0] * 90, "2": [0] * 90, "3": [0] * 90, "4": [0] * 90}
            extent_nat = {"1": [0] * 90, "2": [0] * 90, "3": [0] * 90, "4": [0] * 90}
            with RadiantLine(lon=eye_lon, lat=eye_lat, r_start=0, r_end=600, direction=int(move_dir)) as radiant:
                arcpy.Intersect_analysis(in_features=["in_memory/select_temp_4_%d" % pid, radiant.temp_name],
                                         out_feature_class="in_memory/extent_temp_%d" % pid, join_attributes="ALL", output_type="INPUT")
                # sr = arcpy.Describe(polygon).spatialReference
                with arcpy.da.SearchCursor("in_memory/extent_temp_%d" % pid, ["SHAPE@", "QUAD", "MOVE", "DEG", "MV_DEG"]) as q:
                    for k in q:
                        quad = k[1]
                        move = k[2]
                        geom = k[0]
                        deg = int(k[3]) % 90
                        mv_deg = int(k[4]) % 90
                        for part in geom.getPart():
                            for pt in part:
                                dist = abs((pt.X + pt.Y * 1j) - (eye_x + eye_y * 1j)) / 1000.0
                                extent_mv[move][mv_deg] = max(extent_mv[move][mv_deg], dist)
                                extent_nat[quad][deg] = max(extent_nat[quad][deg], dist)
                extent_mv_str += "%.2f|%.2f|%.2f|%.2f" % (sum(extent_mv["1"]) / 90.0, sum(extent_mv["2"]) / 90.0, sum(extent_mv["3"]) / 90.0, sum(extent_mv["4"]) / 90.0)
                extent_str += "%.2f|%.2f|%.2f|%.2f" % (sum(extent_nat["1"]) / 90.0, sum(extent_nat["2"]) / 90.0, sum(extent_nat["3"]) / 90.0, sum(extent_nat["4"]) / 90.0)
            extent_mv_str += ","
            extent_str += ","

        # Get largest polygons and copy their attributes
        all_fields = [p.name for p in arcpy.ListFields(polygon)][2:]  # The first is always id, second is always shape
        area_index = all_fields.index("AREA")
        max_area = 0
        with arcpy.da.SearchCursor(polygon, all_fields, where_clause="dBZ=%d" % l) as cur:
            for row in cur:
                if row[area_index] > max_area:
                    max_area = area_index
                    attr = row   # row is a tuple
        large_attr_list.append(row)
        
    
    # We need again process large_attr_list to conver to csv strings
    large_str = [",".join(map(str, t)) for t in zip(*large_attr_list)]

    arcpy.Delete_management("in_memory")

    # let us return field name first, then field values
    return (["dispersiveness", "closure", "frag", "asymmetry", "dis_e", "dis_n", "extent_move", "extent_geom"] + all_fields, 
            [dispersiveness, closure_str, fragmentation, roundness, displacements_n, displacements_e, extent_mv_str, extent_str] + large_str)


def add_track_position(polygon, timestamp, track_dict):
    arcpy.AddField_management(polygon, "EYE_X", "DOUBLE")
    arcpy.AddField_management(polygon, "EYE_Y", "DOUBLE")
    arcpy.AddField_management(polygon, "TO_EYE", "DOUBLE")
    arcpy.AddField_management(polygon, "CVX_TO_EYE", "DOUBLE")
    arcpy.AddField_management(polygon, "ANGLE", "DOUBLE")
    arcpy.AddField_management(polygon, "DIR", "LONG")
    x0, y0 = track_dict[timestamp]["pos"]
    move = track_dict[timestamp]["dir"]


    # We need apply a buffer clip at this stage, 600km should be large enough
    sr = arcpy.Describe(polygon).spatialReference
    arcpy.CreateFeatureclass_management("in_memory", "buffer_point", "POINT", spatial_reference=sr)
    pt = arcpy.PointGeometry(arcpy.Point(x0, y0), sr)
    with arcpy.da.InsertCursor("in_memory\\buffer_point", ["SHAPE@"]) as cur:
        cur.insertRow([arcpy.PointGeometry(arcpy.Point(x0, y0))])
    arcpy.Buffer_analysis("in_memory\\buffer_point", "in_memory\\buffer_area", buffer_distance_or_field="600 Kilometers",
                          line_side="FULL", line_end_type="ROUND", dissolve_option="ALL", dissolve_field="", method="GEODESIC")
    arcpy.Clip_analysis(polygon, "in_memory\\buffer_area", "in_memory\\clip_area")
    arcpy.CopyFeatures_management("in_memory\\clip_area", polygon)
    add_basic_geometry_attr(polygon)

    with arcpy.da.UpdateCursor(polygon,
                               ["SHAPE@", "CNTRX", "CNTRY",
                                "TO_EYE", "CNTRX_CVX", "CNTRY_CVX",
                                "CVX_TO_EYE", "EYE_X", "EYE_Y", "ANGLE", "DIR"]) as cur:
        for row in cur:
            row[3], row[9] = line_dist((x0, y0), (row[1], row[2]))
            # row[6] = line_dist((x0, y0), (row[4], row[5]))
            row[7] = x0
            row[8] = y0
            row[10] = int(move)
            cur.updateRow(row)

    print("%s: polygon distance to eye; convex hull distance to eye; closure" % polygon)


def clean_fields(polygon):
    F = arcpy.ListFields(polygon)
    for field in F:
        if field.name.find("_1") != -1:
            arcpy.DeleteField_management(polygon, field.name)
            print("%s: Field %s deleted" % (polygon, field.name))
    pass


def execute(input_feat, output_feat, track_dict, date_format, levels=(20, 25, 30, 35, 40), prefix_start=0,
            prefix_end=15):
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = "in_memory"
    try:
        # Copy to destination
        arcpy.CopyFeatures_management(input_feat, output_feat)
        print("Copying %s -> %s" % (input_feat, output_feat))
        # Get timestamp
        q = os.path.basename(input_feat)
        timestamp = time.mktime(utils.smart_lookup_date(q, date_format).timetuple())
        # Add distance to track
        add_track_position(output_feat, timestamp, track_dict)
        # Clean fields
        clean_fields(output_feat)
        # Dispersivness and EVERYTHING
        move = track_dict[timestamp]["dir"]
        dispersive = generate_dispersiveness(output_feat, levels, move_dir=move)
        print("OK", dispersive)
        return dispersive
    except Exception as ex:
        logging.exception(ex.message)
        return "Error"


def main(workspace, date_format="%Y%m%d_%H%M%S", track_pickle=None):
    stage1 = utils.stage1_folder
    stage2 = utils.stage2_folder

    utils.create_dirs([stage2])

    track_pickle = track_pickle or utils.track_pickle
    track_dict = pickle.load(open(track_pickle))

    error_list = []

    output_file = open(os.path.join(utils.work_base_folder, "Dispersiveness.csv"), "w")
    output_file.write("date_string,dispersiveness\n")

    for q in utils.list_folder_sorted_ext(folder=stage1, ext=".shp"):
        f = os.path.join(stage1, q)
        adv_feature = utils.relocate(q, stage2)
        r = execute(f, adv_feature, track_dict, date_format)
        if r is None:
            error_list.append(r)
        else:
            output_file.write("%s,%f\n" % (q, r))

    output_file.close()

    print("Done")
    print("Errors:", error_list)
