import json

import geopandas as gpd
import pandas as pd

from utilities.utilities import automkdir


def get_points_file(points_file):
    print(f"Reading {points_file}")
    points_file = gpd.read_file(points_file)
    points = points_file.geometry.explode(index_parts=False).to_list()
    points = {(int(round(pt.x)), int(round(pt.y))) for pt in points}
    points = list(points)
    print(f"Done Reading {points_file}")
    return points


def read_json(file):
    with open(file) as jsnfle:
        return json.load(jsnfle)


def write_json(file, data):
    automkdir(file)
    with open(file, "w") as jsnfle:
        json.dump(data, jsnfle, indent=4)


def read_waypoint_file(waypoint_file):
    if isinstance(waypoint_file, list):
        data = []
        for file in waypoint_file:
            data.extend(read_waypoint_file(file))
        return data
    waypoints = pd.read_csv(waypoint_file)
    waypoints = list(set(tuple([int(i) for i in x]) for x in waypoints.to_records(index=False)))
    return waypoints


def read_sbw_file(sbws, crs):
    sbws = read_geo_files_into_geopandas(sbws, crs)
    sbws = sbws[sbws['GTYPE'] == 'P']
    sbws = _geopandas_fix_datetime(sbws,
                                   cols=['ISSUED', 'EXPIRED', 'INIT_ISS', 'INIT_EXP'],
                                   fmt='%Y%m%d%H%M%S')
    return sbws


def _geopandas_fix_datetime(gdf, cols=None, fmt='%Y%m%d%H%M%S'):
    """Adds date time to :param cols: in a :param gdf: geopandas dataframe.  :param fmt: is the datetime format"""
    if isinstance(cols, str):
        gdf[cols] = pd.to_datetime(gdf[cols], format=fmt)
    else:
        for col in cols:
            gdf[col] = pd.to_datetime(gdf[col], format=fmt)
    return gdf


def read_geo_files_into_geopandas(files, crs="EPSG:4326"):
    if isinstance(files, str):
        print(f"Reading : {files}")
        gp_df = gpd.read_file(files)
        if gp_df.crs is None:
            gp_df = gp_df.set_crs(crs=4326)
        gp_df = gp_df.to_crs(crs=crs)
        return gp_df
    gp_df = []
    for file in files:
        print(f"Reading : {file}")
        gp_df.append(gpd.read_file(file))
        gp_df[-1] = gp_df[-1].to_crs(crs=crs)
    gp_df = pd.concat(gp_df)
    print(f"Done Reading! : {files}")
    return gp_df
