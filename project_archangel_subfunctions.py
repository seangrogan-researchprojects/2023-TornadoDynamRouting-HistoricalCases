import concurrent.futures
import datetime
from time import strptime

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point
# from shapely import Point, Polygon
from tqdm import tqdm, trange

from utilities.file_io import read_sbw_file, read_geo_files_into_geopandas, get_points_file, read_json, write_json
from utilities.pickles_io import read_pickle, write_pickle
from utilities.utilities import flatten_a_list


def get_historical_cases_data(pars):
    pickle_file = f"{pars['pickle_base']}/historical_data_pickle.pickle"
    data = read_pickle(pickle_file)
    if data is not None:
        sbws, damage_polygons, dates = data
        return sbws, damage_polygons, dates
    points = get_points_file(pars['points_file'])
    print(f"Reading SBWs {pars['sbws']}")
    sbws = read_sbw_file(pars['sbws'], pars['crs'])
    print(f"Reading Damage Polygons {pars['damage_polygons']}")
    damage_polygons = read_geo_files_into_geopandas(pars['damage_polygons'], pars['crs'])
    print("fin")
    sbws, damage_polygons, dates = separate_to_tornado_cases(points, damage_polygons, sbws)
    write_pickle(pickle_file, (sbws, damage_polygons, dates))
    return sbws, damage_polygons, dates


def separate_to_tornado_cases(waypoints, damage_polygons, sbws):
    sbws = sbws[sbws['PHENOM'] == 'TO']
    damage_polygons = damage_polygons[damage_polygons['stormdate'].notnull()]
    sbws, damage_polygons, dates = collate_events(sbws, damage_polygons)
    temp_waypoints = pd.DataFrame(data=waypoints, index=waypoints, columns=['x', 'y'])
    with tqdm(total=len(sbws), desc="Attaching waypoints to SBWs", leave=False) as pbar:
        sbws['waypoints'] = \
            sbws.apply(
                lambda x: filter_points(temp_waypoints, x, pbar),
                axis=1,
                result_type='reduce')
    sbws.dropna(axis=0, how='any', subset=['waypoints'], inplace=True)
    sbws, damage_polygons, dates = collate_events(sbws, damage_polygons)
    return sbws, damage_polygons, dates


def filter_points(waypoints, geom, pbar=None):
    if pbar:
        pbar.update()
    minx, miny, maxx, maxy = geom.geometry.bounds
    dx = 1 + abs(maxx - minx) // 2
    dy = 1 + abs(maxy - miny) // 2
    waypoints = waypoints[
        (waypoints.x >= minx - dx) & (waypoints.x <= maxx + dx) &
        (waypoints.y >= miny - dy) & (waypoints.y <= maxy + dy)
        ]
    test = list(pt for pt in waypoints.index.tolist() if geom.geometry.contains(Point(pt[0], pt[1])))
    if len(test) <= 0:
        return np.NaN
    _waypoints = list(pt for pt in waypoints.index.tolist())
    if _waypoints:
        return _waypoints
    return np.NaN


def collate_events(sbws, damage_polygons):
    sbw_cases = []
    tor_cases = []
    sbws['issued_date'] = sbws['ISSUED'].dt.date
    sbws['event_date'] = sbws['ISSUED'].dt.date
    damage_polygons['stormdate'] = pd.to_datetime(damage_polygons['stormdate'], format="%Y-%m-%d")
    damage_polygons['stormdate'] = damage_polygons['stormdate'].dt.date
    damage_polygons['event_date'] = damage_polygons['stormdate']
    tornado_dates = set(damage_polygons['stormdate'].to_list())
    sbw_dates = set(sbws['issued_date'].to_list())
    _dates = sorted(list(tornado_dates.intersection(sbw_dates)))
    for date in tqdm(sorted(list(_dates), reverse=True), desc="Checking Events"):
        temp_tornado_db, temp_sbws = damage_polygons[damage_polygons['stormdate'] == date], sbws[
            sbws['issued_date'] == date]
        _temp_torn = temp_tornado_db[
            pd.concat([temp_tornado_db.intersects(row.geometry) for idx, row in temp_sbws.iterrows()], axis=1).max(
                axis=1)]
        _temp_sbw = []
        for idx, row in temp_tornado_db.iterrows():
            __temp = temp_sbws[
                pd.concat([temp_sbws.intersects(row.geometry)], axis=1).max(
                    axis=1)]
            if len(__temp) > 0:
                _temp_sbw.append(__temp)
        if len(_temp_sbw) > 0:
            _temp_sbw = pd.concat(_temp_sbw)
            sbw_cases.append(_temp_sbw)
        tor_cases.append(_temp_torn)
    _tor_cases = pd.concat(tor_cases)
    _sbw_cases = pd.concat(sbw_cases)
    return _sbw_cases, _tor_cases, _dates


def create_waypoints_data_tables(base_pars, dynamic_pars, damage, sbws, date, *args, **kwargs):
    print("\n")
    print(f"Working on Waypoint Data Table for {date}")
    waypoints = list(set(flatten_a_list(sbws.waypoints.to_list())))
    waypoints_data_table = read_pickle(f"./pickles/waypoints_data_table/{date}.pickle")
    if waypoints_data_table is None:
        if len(waypoints) < 1_000:
            waypoints_data_table = create_waypoints_data_table(waypoints,
                                                               damage, sbws, base_pars["r_scan"],
                                                               dynamic_pars["default_score"])
        else:
            print(f"Using Multiprocessing!")
            print(f"N_Wpts {len(waypoints)}")
            waypoints_data_table = create_waypoints_data_table_mp(waypoints, damage, sbws, base_pars["r_scan"],
                                                                  dynamic_pars["default_score"])
        write_pickle(f"./pickles/waypoints_data_table/{date}.pickle", waypoints_data_table)
    print(f"Completed {date}!")
    return waypoints_data_table, waypoints


def create_waypoints_data_table_mp(waypoints, damage, sbws, r_scan, default_score, bin_width=100):
    with concurrent.futures.ProcessPoolExecutor() as ppe:
        waypoint_bins = [waypoints[x:x + bin_width] for x in trange(0, len(waypoints), bin_width,
                                                                    desc=f"Separating into {str(1 + len(waypoints) // bin_width)}")]
        print(f"N_Bins {len(waypoint_bins)}")
        cases = [dict(waypoints=waypoint_bin,
                      damage=damage,
                      sbws=sbws,
                      r_scan=r_scan,
                      default_score=default_score,
                      k=k + 1,
                      total=len(waypoint_bins)) for k, waypoint_bin in
                 enumerate(tqdm(waypoint_bins, desc="Submitting"))]
        results = [ppe.submit(create_waypoints_data_table_wrapper, kwargs=case) for case in cases]
        data = []
        for f in tqdm(concurrent.futures.as_completed(results), desc="Getting MP Results"):
            data.append(f.result())
    return pd.concat(data)


def create_waypoints_data_table_wrapper(args=None, kwargs=None):
    if args and not kwargs:
        return create_waypoints_data_table(*args)
    elif not args and kwargs:
        return create_waypoints_data_table(**kwargs)
    else:
        return create_waypoints_data_table(*args, **kwargs)


def create_waypoints_data_table(waypoints, damage, sbws, r_scan, default_score, k=None, total=None):
    def is_inside(_point, _geoms, _r_scan):
        if isinstance(_geoms, gpd.GeoDataFrame) or isinstance(_geoms, pd.DataFrame):
            _geoms = _geoms.geometry.to_list()
        if isinstance(_geoms, Polygon):
            _geoms = [_geoms]
        return any(geom.contains(Point(_point[0], _point[1])) for geom in _geoms) or any(
            geom.distance(Point(_point[0], _point[1])) <= _r_scan for geom in _geoms)

    total_data = ""
    if total is not None:
        total_data = f" {k: >{len(str(total))}}/{total}"
    elif k is not None:
        total_data = f" {k}"
    data = {
        waypoint: {
            "damaged": is_inside(waypoint, damage, r_scan),
            "in_sbw": is_inside(waypoint, sbws, r_scan),
            "score": default_score * is_inside(waypoint, sbws, r_scan),
            "base_score": default_score * is_inside(waypoint, sbws, r_scan),
            "group_score": default_score * is_inside(waypoint, sbws, r_scan),
            "visited": False,
            "_wp": waypoint,
            "_wp_x": waypoint[0],
            "_wp_y": waypoint[1],
        }
        for waypoint in tqdm(waypoints, desc=f"Generating Waypoint Data Table{total_data}")
    }
    return pd.DataFrame(data).transpose()


def read_write_dates_completed_file(file=None, data=None):
    if file is None:
        file = "./datafiles/dates_completed.json"
    if data is None:
        try:
            dates_completed = read_json(file)
            dates_completed = [strptime(ele, "%Y-%m-%d") for ele in dates_completed]
            dates_completed = [datetime.date(ele.tm_year, ele.tm_mon, ele.tm_mday) for ele in dates_completed]
            return dates_completed
        except:
            return []
    else:
        data = [ele.strftime('%Y-%m-%d') for ele in data]
        write_json(file, data)