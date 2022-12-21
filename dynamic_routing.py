import math
import random
import warnings

import pandas as pd
from scipy.spatial.distance import squareform, pdist
from shapely.geometry import LineString, Point, MultiLineString
from tqdm import tqdm

from influence_matrix_creators import create_symmetric_influence_matrix, plot_influence_matrix_helper, \
    create_data_driven_influence_matrix
from utilities.plotter_utilities import plot_influence_matrix, plotter_utilities_mp, plot_route_and_wp_scores
from route_nearest_insertion import route_nearest_insertion
from utilities.utilities import datetime_string, euclidean


def initial_influence_matrix_to_use(pars):
    if pars["influence_matrix_type"] in {"data-driven", "data-driven-first"}:
        return "data-driven"
    if pars["influence_matrix_type"] in {"symmetric", "symmetric-first"}:
        return "symmetric"


def dynamic_routing(waypoints_data, pars, random_seed, BASE_OUTPUT_FOLDER):
    routing_mode = pars["routing_mode"]

    waypoints = waypoints_data._wp.to_list()
    dist_matrix = pd.DataFrame(squareform(pdist(waypoints)), columns=waypoints, index=waypoints)
    influence_matrix = dict()
    if pars["influence_matrix_type"] == True:
        pars["influence_matrix_type"] = "symmetric"
    if pars["influence_matrix_type"].lower() in {"symmetric", "symmetric-first", "data-driven-first"}:
        influence_matrix["symmetric"] = create_symmetric_influence_matrix(
            waypoints, dist_matrix, pars["max_influence"], pars["min_influence"], pars
        )
        matrix_type = "symmetric"
        if pars['plots'] in {'all', 'main'}:
            plot_influence_matrix_helper(waypoints, influence_matrix[matrix_type], 0,
                                     BASE_OUTPUT_FOLDER, matrix_type)
    if pars["influence_matrix_type"].lower() in {"data-driven", "symmetric-first", "data-driven-first"}:
        influence_matrix["data-driven"] = create_data_driven_influence_matrix(
            waypoints, dist_matrix, pars["max_influence"], pars["min_influence"],
            pars["tornado_data_file"], pars["mag_limit"], pars["bin_width"], pars
        )
        matrix_type = "data-driven"
        if pars['plots'] in {'all', 'main'}:
            plot_influence_matrix_helper(waypoints, influence_matrix[matrix_type], 0,
                                     BASE_OUTPUT_FOLDER, matrix_type)
    initial_waypoints_to_route = list(waypoints_data[waypoints_data['in_sbw'] == True].index)
    if pars["init_route"]:
        tour, dist_init = route_nearest_insertion(initial_waypoints_to_route)
    else:
        tour = get_init_dynamic_tour(pars, waypoints_data, dist_matrix, influence_matrix, waypoints)
        dist_init = None
    p_bar = tqdm(desc=f"Running Dynamic Program {routing_mode}", total=len(tour))

    idx = 0
    route_as_visited = []

    short_memory = list()
    long_memory = list()
    all_memory = list()
    candidate_waypoints = list()

    influence_matrix_to_use = initial_influence_matrix_to_use(pars)

    while len(tour) > 0:
        if idx >= len(waypoints_data) - 1:
            break
        idx += 1
        p_bar.set_postfix_str(
            f"LenTour {len(route_as_visited)} | nxtWpts {len(tour)} | nCandWpts {len(candidate_waypoints)}")
        p_bar.update()

        next_waypoint = tour.pop(0)
        route_as_visited.append(next_waypoint)
        waypoints_data.at[next_waypoint, "visited"] = True
        if waypoints_data.loc[[next_waypoint]].damaged.bool():
            waypoints_data.at[next_waypoint, 'score'] = 1
            waypoints_data.at[next_waypoint, 'base_score'] = pars["base_scores"]["visited"]["damaged"]
            short_memory.append(True)
            long_memory.append(True)
            all_memory.append(True)
            if pars["influence_matrix_type"] in {"symmetric-first"}:
                influence_matrix_to_use = "data-driven"
            if pars["influence_matrix_type"] in {"data-driven-first"}:
                influence_matrix_to_use = "symmetric"
        else:
            waypoints_data.at[next_waypoint, 'score'] = 0
            waypoints_data.at[next_waypoint, 'base_score'] = pars["base_scores"]["visited"]["undamaged"]
            short_memory.append(False)
            long_memory.append(False)
            all_memory.append(False)
        if pars['plots'] in {'all'} or any(short_memory) or len(tour) <= 0:
            waypoints_data = update_scores(waypoints_data,
                                       influence_matrix[influence_matrix_to_use],
                                       dist_matrix,
                                       pars["max_influence"], update_group_score=False)
        while len(short_memory) > pars["short_memory_length"]:
            short_memory.pop(0)
        while len(long_memory) > pars["long_memory_length"]:
            long_memory.pop(0)
        if any(short_memory) or len(tour) <= 0:
            candidate_waypoints = waypoints_data[(waypoints_data['score'] > pars["min_score_to_consider"])
                                                 & (waypoints_data['visited'] == False)]
            p_bar.set_postfix_str(
                f"LenTour {len(route_as_visited)} | nxtWpts {len(tour)} | nCandWpts {len(candidate_waypoints)}")
            tour = update_route_function(tour, candidate_waypoints,
                                         waypoints_data, dist_matrix, route_as_visited, pars,
                                         mode=routing_mode)
            if routing_mode != "do_nothing" and len(tour) > 0:
                waypoints_along_route = get_candidate_waypoints_for_long_arcs(
                    route_as_visited, tour, candidate_waypoints, dist_matrix, pars["max_influence"]
                )
                tour = update_route_function(tour, waypoints_along_route,
                                             waypoints_data, dist_matrix, route_as_visited, pars,
                                             influence_matrix=influence_matrix,
                                             mode="nearest_insertion",
                                             last_wp=route_as_visited[-1])
                tour = tour[1:]
            if pars["init_route"] and not any(long_memory) and len(candidate_waypoints) > len(tour):
                tour = update_route_function(tour, candidate_waypoints,
                                             waypoints_data, dist_matrix, route_as_visited, pars,
                                             influence_matrix=influence_matrix,
                                             mode="nearest_insertion",
                                             last_wp=route_as_visited[-1])
        if pars['plots'] in {'all'}:
            plotter_utilities_mp(plot_route_and_wp_scores, kwargs=dict(
                waypoints_data=waypoints_data,
                route_as_visited=route_as_visited, route_to_visit=tour,
                show=False, title=f"Route At {idx}",
                path=f"{BASE_OUTPUT_FOLDER}/plots/routes/route_{idx:05d}.png"
            ), mp=False)
    missed_waypoints = waypoints_data[
        (waypoints_data['visited'] == False) &
        (waypoints_data['damaged'] == True)
        ]
    if pars['plots'] in {'all', 'main'}:
        plotter_utilities_mp(plot_route_and_wp_scores, kwargs=dict(
        waypoints_data=waypoints_data,
        route_as_visited=route_as_visited, route_to_visit=tour,
        show=False, title=f"Route At {idx}",
        path=f"{BASE_OUTPUT_FOLDER}/plots/routes/route_{idx:05d}.png"
    ), mp=False)
    return route_as_visited, all_memory, len(missed_waypoints), dist_init


def get_candidate_waypoints_for_long_arcs(route_as_visited, init_tour, waypoints_data, dist_matrix, influence_range):
    current_wp, next_wp = route_as_visited[-1], init_tour[0]
    line = LineString([current_wp, next_wp])
    influence_range = min(influence_range, line.length / 2)
    left = line.parallel_offset(influence_range, 'left')
    right = line.parallel_offset(influence_range, 'right')
    hull = MultiLineString([line, left, right]).convex_hull
    candidates = waypoints_data._wp.to_list()
    pts_in_range = [c for c in candidates if hull.contains(Point(c))] + [next_wp]
    pts_in_range = list(set(pts_in_range))
    # pts_in_range.append(current_wp)
    pts_in_range.append(next_wp)
    candidate_waypoints = waypoints_data.loc[pts_in_range]
    return candidate_waypoints


def update_route_function(init_tour, candidate_waypoints,
                          waypoints_data, dist_matrix, route_as_visited, pars,
                          mode='do_nothing', influence_matrix=None, last_wp=None):
    mode = mode.lower()
    new_tour = list()
    _wp = route_as_visited[-1]
    if len(candidate_waypoints) <= 1:
        new_tour = candidate_waypoints.sort_values('score', ascending=False)["_wp"].to_list()
        return new_tour
    # waypoints_to_visit = waypoints_data[(waypoints_data['in_sbw'] == True) & (waypoints_data['visited'] == False)]
    if mode in {'do_nothing'}:
        new_tour = init_tour[:]
    elif mode in {'order_scores', 'scores_in_order'}:
        new_tour = candidate_waypoints.sort_values('score', ascending=False)["_wp"].to_list()[:5]
    elif mode in {'group_scores_in_order'}:
        candidate_waypoints = update_scores(waypoints_data,
                                            influence_matrix,
                                            dist_matrix,
                                            pars["max_influence"], update_group_score=True)
        new_tour = candidate_waypoints.sort_values('group_score', ascending=False)["_wp"].to_list()
    elif mode in {'ni', 'nearest_insertion'}:
        new_tour, dist = route_nearest_insertion(candidate_waypoints["_wp"].to_list(),
                                                 start_min_arc=True, start_at=last_wp)
    elif mode in {'dcf_by_dist', 'dcf_by_distance'}:
        ...  # todo
    else:
        if not bool(mode):
            warnings.warn(f"the parameter 'mode' is empty")
        raise NotImplementedError(f"Mode {mode} is not implemented!")
    return new_tour


def update_scores(waypoints_data, influence_matrix, distance_matrix,
                  influence_range, update_group_score=True):
    def __update_waypoint_score(_row, _waypoints_data, _influence_matrix):
        if _row.visited and _row.damaged:
            return 1
        if _row.visited and not _row.damaged:
            return 0
        wp = _row["_wp"]
        score = _influence_matrix[wp].multiply(_waypoints_data['base_score']).sum() / _influence_matrix[wp].sum()
        return min(max(score, 0), 1)

    def __update_waypoint_group_score(_row, _waypoints_data, _distance_matrix, _influence_range):
        if _row.visited and _row.damaged:
            return 1
        if _row.visited and not _row.damaged:
            return 0
        wp = _row["_wp"]
        nearby_wpts = list(_distance_matrix[wp][_distance_matrix[wp] <= _influence_range].index)
        score = _waypoints_data.loc[nearby_wpts]['score'].mean()
        return min(max(score, 0), 1)

    waypoints_data['score'] = waypoints_data.apply(
        lambda row: __update_waypoint_score(row, waypoints_data, influence_matrix),
        axis=1
    )
    if update_group_score:
        waypoints_data['group_score'] = waypoints_data.apply(
            lambda row: __update_waypoint_group_score(row, waypoints_data, distance_matrix, influence_range),
            axis=1
        )
    return waypoints_data


def get_init_dynamic_tour(pars, waypoints_data, dist_matrix, influence_matrix, waypoints):
    target = (0, 0)
    closest_to_target = {wp: euclidean(wp, (target[0], target[1])) for wp in waypoints}
    target = min(closest_to_target, key=closest_to_target.get)
    candidate_waypoints, _mstc = list(), pars["min_score_to_consider"]

    while len(candidate_waypoints) <= 0:
        candidate_waypoints = waypoints_data[(waypoints_data['score'] > _mstc)
                                             & (waypoints_data['visited'] == False)]
        _mstc = _mstc * .95
    new_tour = update_route_function(None, candidate_waypoints,
                                     waypoints_data, dist_matrix, [target, ], pars,
                                     mode='order_scores', influence_matrix=influence_matrix,
                                     last_wp=target)
    candidate_waypoints = candidate_waypoints[candidate_waypoints._wp != target]
    waypoints_along_route = get_candidate_waypoints_for_long_arcs(
        [target, ], new_tour, candidate_waypoints, dist_matrix, pars["max_influence"]
    )
    tour = update_route_function(None, waypoints_along_route,
                                 waypoints_data, dist_matrix, [target, ], pars,
                                 influence_matrix=influence_matrix,
                                 mode="nearest_insertion",
                                 last_wp=target)
    tour = [target] + tour
    return tour
