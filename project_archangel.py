import concurrent.futures
import csv
import datetime
import os
import time
import socket

import pandas as pd
import geopandas as gpd
from shapely import Polygon, affinity, Point
from tqdm import tqdm, trange

from pars.parfile_reader import parfile_reader
from project_archangel_subfunctions import get_historical_cases_data, get_events_by_date, make_minimum_cases, \
    make_pois_by_date, get_waypoints, create_waypoints_data_tables
from utilities.pickles_io import read_pickle, write_pickle
from utilities.plotter_utilities import plot_with_polygon_case, plot_route_and_wp_scores
from utilities.utilities import automkdir, datetime_string
from waypoint_creators.waypoint_creators import create_waypoints


def project_archangel(parfile):
    pars = parfile_reader(parfile)
    sbws, damage_polygons, dates = get_historical_cases_data(pars)
    events_by_date = get_events_by_date(pars, damage_polygons, sbws, dates)
    events_by_date = make_minimum_cases(dates, events_by_date, pars)
    pois_by_date = make_pois_by_date(dates, sbws, pars)

    log_file_path = f"./logs/log_{socket.gethostname()}_{datetime_string()}.csv"
    for date in dates:
        print(f"Working On {date}")
        for key, sub_event in events_by_date[date].items():
            start_t = time.time()
            print(f"Working On Sub-Event {date} - {key}")
            poi = pois_by_date[date]
            dynamic_routing(pars, date, key, sub_event, poi)
            t_sec = time.time() - start_t
            log_results(log_file_path, pars, date, key, t_sec)


def dynamic_routing(pars, date, sub_event_id, sub_event, poi):
    sbws, damage = sub_event['sbws'], sub_event['damage']
    waypoints = get_waypoints(pars, date, poi)
    waypoint_data_table = create_waypoints_data_tables(pars, waypoints, sbws, damage, date)
    bounds = get_bounds(damage, sbws)
    plot_with_polygon_case(waypoints=waypoints,
                           sbw=sbws,
                           damage_poly=damage,
                           bounds=bounds,
                           show=False, title=f"{date} | {sub_event_id}",
                           path=f"./plots/plots_case_data/{date}_{sub_event_id}.png")
    plot_route_and_wp_scores(
        waypoint_data_table, route_as_visited=None, route_to_visit=None,
        show=False,
        title=f"{date} | {sub_event_id}",
        path=f"./plots/plots_waypoints_data/{date}_{sub_event_id}.png",
        sbw=sbws, bounds=bounds
    )
    return 0

def get_bounds(damage, sbws):
    polys = damage+sbws
    bound_data = [p.bounds for p in polys]
    minx, miny, maxx, maxy = zip(*bound_data)
    lb_x, ub_x, lb_y, ub_y = min(minx), max(maxx), min(miny), max(maxy)
    return [lb_x, ub_x, lb_y, ub_y]


def log_results(log_file_path, pars, date, sub_event, t_sec):
    data = [
        ("date", str(date)),
        ("sub_event", str(sub_event)),
        ("t_sec", str(t_sec)),
    ]

    data += list(pars.items())
    header, row = zip(*data)
    automkdir(log_file_path)
    if os.path.exists(log_file_path):
        header = False
    with open(log_file_path, 'a', newline='') as logfile:
        writer = csv.writer(logfile)
        if header:
            writer.writerow(header)
        writer.writerow(row)


if __name__ == '__main__':
    project_archangel("./pars/par0.json")
