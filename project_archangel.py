import csv
import datetime
import os
import time
import socket

import pandas as pd
import geopandas as gpd
from tqdm import tqdm

from pars.parfile_reader import parfile_reader
from project_archangel_subfunctions import get_historical_cases_data, get_events_by_date, make_minimum_cases
from utilities.pickles_io import read_pickle, write_pickle
from utilities.plotter_utilities import plot_with_polygon_case
from utilities.utilities import flatten_a_list, automkdir, datetime_string


def project_archangel(parfile):
    pars = parfile_reader(parfile)
    sbws, damage_polygons, dates = get_historical_cases_data(pars)
    events_by_date = get_events_by_date(pars, damage_polygons, sbws, dates)
    events_by_date = make_minimum_cases(dates, events_by_date, pars)

    log_file_path = f"./logs/log_{socket.gethostname()}_{datetime_string()}.csv"
    for date in dates:
        print(f"Working On {date}")
        for key, sub_event in events_by_date[date].items():
            start_t = time.time()
            print(f"Working On Sub-Event {date} - {key}")
            poi = list(set(flatten_a_list(sbws[sbws.event_date == date].waypoints.to_list())))
            dynamic_routing(pars, sub_event, poi)
            t_sec = time.time() - start_t
            log_results(log_file_path, date, key, t_sec)


def dynamic_routing(pars, sub_event, poi):
    return 0


def log_results(log_file_path, date, sub_event, t_sec):
    data = [
        ("date", str(date)),
        ("sub_event", str(sub_event)),
        ("t_sec", str(t_sec)),
    ]
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
