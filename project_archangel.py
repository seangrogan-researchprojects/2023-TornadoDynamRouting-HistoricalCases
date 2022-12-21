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
    make_pois_by_date, get_waypoints, create_waypoints_data_tables, get_bounds, plot_stuff
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
            log_results(log_file_path, pars, date, key, t_sec, len(sub_event['damage']))


def dynamic_routing(pars, date, sub_event_id, sub_event, poi):
    sbws, damage = sub_event['sbws'], sub_event['damage']
    waypoints = get_waypoints(pars, date, poi)
    waypoint_data_table = create_waypoints_data_tables(pars, waypoints, sbws, damage, date)
    plot_stuff(damage, sbws, date, waypoints, sub_event_id, waypoint_data_table)
    return 0


def log_results(log_file_path, pars, date, sub_event, t_sec, n_damage_polys):
    data = [
        ("date", str(date)),
        ("sub_event", str(sub_event)),
        ("t_sec", str(t_sec)),
        ("n_damage_polys", n_damage_polys)
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
