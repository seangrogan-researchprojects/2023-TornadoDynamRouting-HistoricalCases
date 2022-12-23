import csv
import os
import time
import socket

from dynamic_routing import perform_dynamic_routing
from pars.parfile_reader import parfile_reader
from project_archangel_subfunctions import get_historical_cases_data, get_events_by_date, make_minimum_cases, \
    make_pois_by_date, get_waypoints, create_waypoints_data_tables, plot_stuff
from route_nearest_insertion import route_nearest_insertion
from utilities.utilities import automkdir, datetime_string, euclidean


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
            route_as_visited, all_memory, n_missed_waypoints, \
            dist_init, minimum_hamiltonian_path, minimum_hamiltonian_path_distance = \
                dynamic_routing(pars, date, key, sub_event, poi)
            t_sec = time.time() - start_t
            log_results(
                log_file_path, pars, date, key, t_sec, len(sub_event['damage']),
                route_as_visited, all_memory, n_missed_waypoints,
                dist_init, minimum_hamiltonian_path,
                minimum_hamiltonian_path_distance
            )


def dynamic_routing(pars, date, sub_event_id, sub_event, poi):
    sbws, damage = sub_event['sbws'], sub_event['damage']
    waypoints = get_waypoints(pars, date, poi)
    waypoint_data_table = create_waypoints_data_tables(pars, waypoints, sbws, damage, date)
    # plot_stuff(damage, sbws, date, waypoints, sub_event_id, waypoint_data_table)
    route_as_visited, all_memory, n_missed_waypoints, dist_init = \
        perform_dynamic_routing(waypoint_data_table, pars)

    waypoints_to_route = waypoint_data_table[waypoint_data_table["damaged"] == True]["_wp"].to_list()
    minimum_hamiltonian_path, minimum_hamiltonian_path_distance = \
        route_nearest_insertion(waypoints_to_route, start_min_arc=False, unknot=True)

    return route_as_visited, all_memory, n_missed_waypoints, dist_init, minimum_hamiltonian_path, minimum_hamiltonian_path_distance


def log_results(log_file_path, pars, date, sub_event, t_sec, n_damage_polys,
                route_as_visited, all_memory, n_missed_waypoints,
                dist_init, minimum_hamiltonian_path,
                minimum_hamiltonian_path_distance
                ):
    dist_of_traveled_route = sum(euclidean(p1, p2)
                                 for p1, p2 in
                                 zip(route_as_visited, route_as_visited[1:]))
    dist_last_damage, \
    dist_first_damage, \
    dist_last_damage, dist_first_damage, wpt_num_last_damage, wpt_num_first_damage = -1, -1, -1, -1, -1, -1
    if any(all_memory):
        for i, (p1, dmg) in enumerate(zip(route_as_visited, all_memory)):
            if dmg:
                wpt_num_first_damage = i
                dist_first_damage = sum(euclidean(p1, p2)
                                        for p1, p2 in
                                        zip(route_as_visited[:i], route_as_visited[1:]))
                break
        for i, (p1, dmg) in enumerate(zip(route_as_visited, all_memory)):
            if dmg:
                wpt_num_last_damage = i
                dist_last_damage = sum(euclidean(p1, p2)
                                       for p1, p2 in
                                       zip(route_as_visited[:i], route_as_visited[1:]))
    n_damaged = sum(all_memory) + n_missed_waypoints
    if dist_last_damage is None or dist_first_damage is None:
        delta_dist, delta_wpt = None, None
        score_as_dist, score_as_wp = None, None
    else:
        delta_dist = dist_last_damage - dist_first_damage
        delta_wpt = wpt_num_last_damage - wpt_num_first_damage
        score_as_dist = delta_dist / max(minimum_hamiltonian_path_distance,1)
        score_as_wp = delta_wpt / n_damaged
    data = [
        ("current_datetime", datetime_string(current=True)),
        ("date", str(date)),
        ("sub_event", str(sub_event)),
        ("t_sec", str(t_sec)),
        ("n_damage_polys", n_damage_polys),
        ("wpt_num_first_damage", wpt_num_first_damage),
        ("dist_first_damage", dist_first_damage),
        ("wpt_num_last_damage", wpt_num_last_damage),
        ("dist_last_damage", dist_last_damage),
        ("delta_dist", delta_dist),
        ("delta_wpt", delta_wpt),
        ("minimum_hamiltonian_path_distance", minimum_hamiltonian_path_distance),
        ("n_damaged", n_damaged),
        ("score_as_dist", score_as_dist),
        ("score_as_wp", score_as_wp),
        ("dist_init", dist_init),
        ("dist_of_traveled_route", dist_of_traveled_route),
        ("n_missed_waypoints", n_missed_waypoints)
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
    project_archangel("./pars/par1.json")
    project_archangel("./pars/par2.json")
    project_archangel("./pars/par3.json")
