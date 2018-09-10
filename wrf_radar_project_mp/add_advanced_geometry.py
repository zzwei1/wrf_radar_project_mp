# coding=utf-8


import os
import datetime
import time
import cPickle
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


def generate_dispersiveness(polygon, levels, workspace="in_memory"):
    arcpy.env.workspace = workspace
    dispersiveness = ""
    closure_str = ""
    fragmentation = ""
    roundness = ""
    adv_elongation = ""
    displacements_e = ""
    displacements_n = ""
    dispersive_search_radius = 500e3

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

        with arcpy.da.SearchCursor(polygon,
                                   ["AREA", "TO_EYE", "SHAPE@", "EYE_X", "EYE_Y", "AREA_CVX", "PERIM", "SUM_AREA", "ANGLE"],
                                   where_clause="dBZ=%d AND TO_EYE<=%f" % (l, dispersive_search_radius)) as cur:
            cur.reset()
            for row in cur:
                # Dispersiveness
                l_dispersive.append([row[0], row[1]])
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

        # Calculate dispersiveness
        areas = numpy.array(l_dispersive)
        if areas.shape != (0,):
            total_areas = numpy.sum(areas[:, 0])
            area_frac = areas[:, 0] / total_areas
            dist_weight = areas[:, 1] / dispersive_search_radius
            dispersiveness += "%f," % numpy.sum(area_frac * dist_weight)
        else:
            dispersiveness += ","

        # Calculate closure
        # Actually we don't need the closure dict in each level, we just need a final number.
        # total_deg = sum(closure.values())
        # if total_deg:
        #     closure_str += "%f," % (total_deg / 360.0)
        # else:
        #     closure_str += ","

        # Calculate fragmentation.
        fareas = numpy.array(l_frag)
        if fareas.shape != (0,):
            total_cvx_areas = numpy.sum(fareas[:, 1])
            solidity = total_areas / total_cvx_areas
            # Connectivity
            sareas = fareas.shape[0]
            conn = 1 - ((sareas - 1) / ((total_areas / 9) ** 0.5 + sareas))
            fragmentation += "%f," % (1 - solidity * conn)
        else:
            fragmentation += ","

        # Asymmetry/Roundness
        # I think, it should be OK for each polygon, but I think it hurt nothing to calculate it here.
        rareas = numpy.array(l_round)
        if fareas.shape != (0,):
            max_rareas = rareas[numpy.argmax(rareas, 0)]
            # R = base_roundness * size_factor
            R = numpy.mean(4 * max_rareas[:, 0] * math.pi / numpy.square(max_rareas[:, 1]) * (
                    numpy.log(max_rareas[:, 0]) / numpy.log(max_rareas[:, 2])))
            roundness += "%f," % (1 - R)
        else:
            roundness += ","

        # Calculate displacement
        areas = numpy.array(l_displace)
        if areas.shape != (0,):
            total_areas = numpy.sum(areas[:, 0])
            area_frac = areas[:, 0] / total_areas
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
            closure_ring_km = [(0, 100), (100, 200), (200, 300), (300, 400), (400, 500)]
            select3 = arcpy.Select_analysis(polygon, "E:\\select_temp_%d.shp" % pid, where_clause="dBZ=%d AND TO_EYE<=600000" % l)
            eye_lon, eye_lat = utils.projFunc(eye_x, eye_y, inverse=True)
            for s, e in closure_ring_km:
                radiant = RadiantLine(lon=eye_lon, lat=eye_lat, r_start=s, r_end=e)
                arcpy.Intersect_analysis(in_features=["E:\\select_temp_%d.shp" % pid, radiant.temp_name],
                                         out_feature_class="E:\\closure_temp_%d.shp" % pid, join_attributes="ALL", output_type="INPUT")
                with arcpy.da.SearchCursor("E:\\closure_temp_%d.shp" % pid, ["SHAPE@"]) as q:
                    count = 0
                    for k in q:
                        count += 1
                    closure_str += "%d|" % count
                # arcpy.Delete_management("E:\\select_temp.shp")
                # arcpy.Delete_management("E:\\closure_temp.shp")
            # Remove last "|"
            if closure_str.endswith("|"):
                closure_str = closure_str[:-1]
            closure_str += ","

        # # Get largest 3 polygons
        # if False:
        # # if _areas_list:
        #     if len(_areas_list) < 3:
        #         _area = min(_areas_list)
        #     else:
        #         _area = sorted(_areas_list)[-3]
        #     # Second pass, get larget N polygons
        #     delete_list = ["in_memory\\L3", "in_memory\\BOX"]
        #     select3 = arcpy.Select_analysis(polygon, delete_list[0], where_clause="AREA>=%f" % _area)
        #     # Get bounding box for entire area
        #     arcpy.MinimumBoundingGeometry_management(delete_list[0], delete_list[1], "RECTANGLE_BY_AREA",
        #                                              mbg_fields_option="MBG_FIELDS", group_option="ALL")
        #     with arcpy.da.SearchCursor(delete_list[1], ["MBG_Width", "MBG_Length"]) as cur2:
        #         for r in cur2:
        #             adv_elongation += "%f," % (row[1] / row[0])
        #
        #     map(arcpy.Delete_management, delete_list)
        # else:
        #     adv_elongation += ","

    return dispersiveness, closure_str, fragmentation, roundness, displacements_n, displacements_e


def add_track_position(polygon, timestamp, track_dict):
    arcpy.AddField_management(polygon, "EYE_X", "DOUBLE")
    arcpy.AddField_management(polygon, "EYE_Y", "DOUBLE")
    arcpy.AddField_management(polygon, "TO_EYE", "DOUBLE")
    arcpy.AddField_management(polygon, "CVX_TO_EYE", "DOUBLE")
    arcpy.AddField_management(polygon, "ANGLE", "DOUBLE")
    x0, y0 = track_dict[timestamp]
    with arcpy.da.UpdateCursor(polygon,
                               ["SHAPE@", "CNTRX", "CNTRY",
                                "TO_EYE", "CNTRX_CVX", "CNTRY_CVX",
                                "CVX_TO_EYE", "EYE_X", "EYE_Y", "ANGLE"]) as cur:
        for row in cur:
            row[3], row[9] = line_dist((x0, y0), (row[1], row[2]))
            # row[6] = line_dist((x0, y0), (row[4], row[5]))
            row[7] = x0
            row[8] = y0
            cur.updateRow(row)
    print "%s: polygon distance to eye; convex hull distance to eye; closure" % polygon


def clean_fields(polygon):
    F = arcpy.ListFields(polygon)
    for field in F:
        if field.name.find("_1") != -1:
            arcpy.DeleteField_management(polygon, field.name)
            print "%s: Field %s deleted" % (polygon, field.name)
    pass


def execute(input_feat, output_feat, track_dict, date_format, levels=(20, 25, 30, 35, 40), prefix_start=0,
            prefix_end=-4):
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = "in_memory"
    try:
        # Copy to destination
        arcpy.CopyFeatures_management(input_feat, output_feat)
        print "Copying %s -> %s" % (input_feat, output_feat)
        # Get timestamp
        q = os.path.basename(input_feat)
        timestamp = time.mktime(datetime.datetime.strptime(q[prefix_start:prefix_end], date_format).timetuple())
        # Add distance to track
        add_track_position(output_feat, timestamp, track_dict)
        # Clean fields
        clean_fields(output_feat)
        # Dispersivness and EVERYTHING
        dispersive = generate_dispersiveness(output_feat, levels)
        print "OK", dispersive
        return dispersive
    except Exception, ex:
        logging.exception(ex.message)
        return "Error"


def main(workspace, date_format="%Y%m%d_%H%M%S", track_pickle=None):
    stage1 = utils.stage1_folder
    stage2 = utils.stage2_folder

    utils.create_dirs([stage2])

    track_pickle = track_pickle or utils.track_pickle
    track_dict = cPickle.load(open(track_pickle))

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

    print "Done"
    print "Errors:", error_list
