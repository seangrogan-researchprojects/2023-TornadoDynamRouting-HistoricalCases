import concurrent.futures
import datetime
from time import strptime

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import affinity
from shapely.geometry import Polygon, Point
from tqdm import tqdm, trange

from utilities.file_io import read_sbw_file, read_geo_files_into_geopandas, get_points_file, read_json, write_json
from utilities.pickles_io import read_pickle, write_pickle
from utilities.plotter_utilities import plot_with_polygon_case, plot_route_and_wp_scores
from utilities.utilities import flatten_a_list, automkdir
from waypoint_creators.waypoint_creators import create_waypoints


def plot_stuff(damage, sbws, date, waypoints, sub_event_id, waypoint_data_table, route_as_visited=None):
    bounds = get_bounds(damage, sbws)
    plot_with_polygon_case(waypoints=waypoints,
                           route=route_as_visited,
                           sbw=sbws,
                           damage_poly=damage,
                           bounds=bounds,
                           show=False, title=f"{date} | {sub_event_id}",
                           path=f"./plots/plots_case_data/{date}_{sub_event_id.replace(':', '-')}.png")
    plot_route_and_wp_scores(
        waypoint_data_table, route_as_visited=route_as_visited,
        route_to_visit=None, damage_poly=damage,
        show=False,
        title=f"{date} | {sub_event_id}",
        path=f"./plots/plots_waypoints_data/{date}_{sub_event_id.replace(':', '-')}.png",
        sbw=sbws, bounds=bounds
    )


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


def make_pois_by_date(dates, sbws, pars):
    pickle_file = f"{pars['pickle_base']}/pois_by_date.pickle"
    pois_by_date = read_pickle(pickle_file)
    if pois_by_date is not None:
        return pois_by_date
    pois_by_date = {date: list(set(flatten_a_list(sbws[sbws.event_date == date].waypoints.to_list()))) for date in
                    tqdm(dates)}
    write_pickle(pickle_file, pois_by_date)
    return pois_by_date


def make_minimum_cases(dates, events_by_date, pars):
    pickle_file = f"{pars['pickle_base']}/events_by_date_less_data.pickle"
    new_events_by_date = read_pickle(pickle_file)
    if new_events_by_date is not None:
        return new_events_by_date
    else:
        new_events_by_date = dict()
    for date in dates:
        print(f"Plotting Information")
        event_data = events_by_date[date]
        output_loc = f"{pars['shapefile_by_date_location']}/{date}"
        automkdir(f"{output_loc}/sbws_{date}.gpkg")

        plot_with_polygon_case(sbw=event_data['sbws'].geometry.to_list(),
                               damage_poly=event_data['damage'].geometry.to_list(),
                               show=False, title=f"{date} | {len(event_data['sbws'])}",
                               path=f"./plots/{date}.png")
        new_events_by_date[date] = make_smaller_events(pars, date, event_data)
    write_pickle(pickle_file, new_events_by_date)
    return new_events_by_date


def make_smaller_events(pars, date, event_data):
    output_loc = f"./separated_plots/"
    cases = []
    for tor_id, tornado in enumerate(event_data['damage'].geometry):
        data = []
        sbws_to_keep = []
        for idx, sbw in event_data['sbws'].iterrows():
            intersection_area = sbw.geometry.intersection(tornado).area
            if intersection_area == 0:
                continue
            area = sbw.geometry.area
            data.append((idx, tor_id, intersection_area, area))
        idx_to_keep = sorted(sorted(data, key=lambda x: x[3]), key=lambda x: x[2], reverse=True)[0][0]
        sbws_to_keep.append(event_data['sbws'].loc[[idx_to_keep]])
        sbws_to_keep = pd.concat(sbws_to_keep)
        assert len(sbws_to_keep.geometry.to_list()) == 1
        cases.append((tornado, sbws_to_keep.geometry.to_list()[0], tor_id))
    tornado, sbw, tor_id = cases.pop(0)
    data_to_return = [[[tornado], [sbw], [tor_id]]]
    while len(cases) > 0:
        update = False
        tornado, sbw, tor_id = cases.pop(0)
        for idx, (t, s, i) in enumerate(data_to_return):
            if any(sbw.intersection(other).area > 0 for other in s):
                t.append(tornado)
                s.append(sbw)
                i.append(tor_id)
                update = True
                break
        if not update:
            data_to_return += [[[tornado], [sbw], [tor_id]]]
    actually_data_to_return = dict()
    for data in data_to_return:
        tornadoes, sbws, tor_ids = data
        tor_id = ":".join(str(t) for t in tor_ids)
        actually_data_to_return[tor_id] = dict(sbws=sbws, damage=tornadoes)
        plot_with_polygon_case(sbw=sbws,
                               damage_poly=tornadoes,
                               show=False,
                               title=f"{date} | {tor_id}",
                               path=f"./plots_separated_v2/{date}_{tor_id.replace(':', '-')}.png")
    return actually_data_to_return


def get_events_by_date(pars, damage_polygons, sbws, dates):
    pickle_file = f"{pars['pickle_base']}/events_by_date.pickle"
    events_by_date = read_pickle(pickle_file)
    if events_by_date is None:
        events_by_date = {
            date: dict(
                damage=damage_polygons[damage_polygons.event_date == date].drop_duplicates(subset=["geometry"]),
                sbws=sbws[sbws.event_date == date].drop_duplicates(subset=["geometry"]),
                date=date,
                n_wpts=len(list(set(flatten_a_list(sbws[sbws.event_date == date].waypoints.to_list()))))
            ) for date in tqdm(dates, desc="Separating Events into Dates")
        }
        for date, event in events_by_date.items():
            dmg_polys = event['damage'].geometry
            indicies_to_asses = dmg_polys.index
            damages_to_asses = sorted([(i, j.geometry) for i, j in event['damage'].iterrows()], key=lambda k: k[1].area,
                                      reverse=True)
            split_tornadoes = dict()
            _id, polygon = damages_to_asses.pop(0)
            split_tornadoes[_id] = polygon
            ids_to_drop = []
            while len(damages_to_asses) > 0:
                _id, polygon = damages_to_asses.pop(0)
                if any(t.intersection(polygon) for t in split_tornadoes.values()):
                    ids_to_drop.append(_id)
                else:
                    split_tornadoes[_id] = polygon
            events_by_date[date]['damage'] = event['damage'].drop(labels=ids_to_drop, axis=0)
        write_pickle(pickle_file, events_by_date)
    return events_by_date


def limit_waypoints(sbws, damage, waypoints, pars):
    polys = sbws + damage
    print(len(waypoints))
    new_waypoints = [
        wp for wp in tqdm(waypoints, desc="spatial limit wpts")
        if any(poly.contains(Point(wp)) for poly in polys)
           or any(poly.distance(Point(wp)) <= pars['max_influence'] * min(pars['near_sbw_scale'], 1) for poly in polys)
    ]
    print(len(new_waypoints))
    return new_waypoints


def create_waypoints_data_tables(pars, waypoints, sbws, damage, date):
    pickle_file = f"{pars['pickle_base']}/waypoints_data_tables/{pars['waypoint_method']}_{pars['r_scan']}/{date}_{pars['waypoint_method']}_{pars['r_scan']}.pickle"
    waypoint_data_table = read_pickle(pickle_file)
    if waypoint_data_table is None:
        if len(waypoints) < 1000:
            waypoint_data_table = create_waypoints_data_table(waypoints, damage, sbws, pars['r_scan'], pars)
        else:
            waypoint_data_table = create_waypoints_data_table_mp(waypoints, damage, sbws, pars['r_scan'], pars)
    return waypoint_data_table


def get_bounds(damage, sbws):
    polys = damage + sbws
    bound_data = [p.bounds for p in polys]
    minx, miny, maxx, maxy = zip(*bound_data)
    lb_x, ub_x, lb_y, ub_y = min(minx), max(maxx), min(miny), max(maxy)
    return [lb_x, ub_x, lb_y, ub_y]


def create_waypoints_data_table_mp(waypoints, damage, sbws, r_scan, pars, bin_width=1000):
    with concurrent.futures.ProcessPoolExecutor() as ppe:
        waypoint_bins = [waypoints[x:x + bin_width] for x in trange(0, len(waypoints), bin_width,
                                                                    desc=f"Separating into {str(1 + len(waypoints) // bin_width)}")]
        print(f"N_Bins {len(waypoint_bins)}")
        cases = [dict(waypoints=waypoint_bin,
                      damage=damage,
                      sbws=sbws,
                      r_scan=r_scan,
                      k=k + 1,
                      pars=pars,
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


def create_waypoints_data_table(waypoints, damage, sbws, r_scan, pars, k=None, total=None):
    def is_inside(_point, _geoms, _r_scan):
        if isinstance(_geoms, gpd.GeoDataFrame) or isinstance(_geoms, pd.DataFrame):
            _geoms = _geoms.geometry.to_list()
        if isinstance(_geoms, Polygon):
            _geoms = [_geoms]
        return any(geom.contains(Point(_point[0], _point[1])) for geom in _geoms) or \
               any(geom.distance(Point(_point[0], _point[1])) <= _r_scan for geom in _geoms)

    def is_nearby(_point, _geoms, _scale, _r_scan=0):
        if _scale is None:
            return 0
        if isinstance(_geoms, gpd.GeoDataFrame) or isinstance(_geoms, pd.DataFrame):
            _geoms = _geoms.geometry.to_list()
        if isinstance(_geoms, Polygon):
            _geoms = [_geoms]
        scaled_geoms = [affinity.scale(_geom, xfact=_scale, yfact=_scale) for _geom in _geoms]
        return is_inside(_point, scaled_geoms, _r_scan)

    total_data = ""
    near_sbw_score = pars["score_near_sbw"]
    default_score = pars["score_in_sbw"]
    if total is not None:
        total_data = f" {k: >{len(str(total))}}/{total}"
    elif k is not None:
        total_data = f" {k}"
    data = {
        waypoint: {
            "damaged": is_inside(waypoint, damage, r_scan),
            "in_sbw": is_inside(waypoint, sbws, r_scan),
            "score": max(default_score * is_inside(waypoint, sbws, r_scan),
                         near_sbw_score * is_nearby(waypoint, sbws, pars["near_sbw_scale"])),
            "base_score": max(default_score * is_inside(waypoint, sbws, r_scan),
                              near_sbw_score * is_nearby(waypoint, sbws, pars["near_sbw_scale"])),
            "group_score": default_score * is_inside(waypoint, sbws, r_scan),
            "visited": False,
            "_wp": waypoint,
            "_wp_x": waypoint[0],
            "_wp_y": waypoint[1],
        }
        for waypoint in tqdm(waypoints, desc=f"Generating Waypoint Data Table{total_data}")
    }
    return pd.DataFrame(data).transpose()


def get_waypoints(pars, date, poi):
    pickle_file = f"{pars['pickle_base']}/waypoints_data/{pars['waypoint_method']}_{pars['r_scan']}/{date}_{pars['waypoint_method']}_{pars['r_scan']}.pickle"
    waypoints = read_pickle(pickle_file)
    if waypoints is None:
        waypoints = create_waypoints(pars, poi, pars['r_scan'], pars['waypoint_method'])
        waypoints = list(waypoints)
        write_pickle(pickle_file, waypoints)
    return waypoints
