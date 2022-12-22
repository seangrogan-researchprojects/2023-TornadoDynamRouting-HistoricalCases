import copy
import itertools
import math
from collections import namedtuple

import numpy as np
import scipy
from shapely.geometry import LineString
from tqdm import tqdm

from utilities.plotter_utilities import plot_route
# from utilities.slides_to_moving_picture_show import make_moving_picture_show
from utilities.utilities import euclidean, datetime_string


def unnkot(route, kounter_limit=float('inf')):
    path = LineString(route)
    kounter = 0
    last_i, last_j = None, None
    last_n, last_m = None, None
    while not path.is_simple and kounter < kounter_limit:
        kounter += 1
        segments = list(zip(route[:-1], route[1:]))
        n_combos = math.comb(len(segments), 2)
        for seg1, seg2 in tqdm(itertools.combinations(segments, 2),
                               desc="Unknoting", position=0, leave=False, total=n_combos,
                               postfix=f"{kounter}|{last_i} -> {last_j}|{last_n} -> {last_m}|{len(route)}"):
            if LineString(seg1).crosses(LineString(seg2)):
                i, j = seg1
                n, m = seg2
                idx_i, idx_j = route.index(i), route.index(j)
                idx_n, idx_m = route.index(n), route.index(m)
                last_i, last_j = idx_i, idx_j
                last_n, last_m = idx_n, idx_m
                route = route[:idx_i + 1] + route[idx_n:idx_j - 1:-1] + route[idx_m:]
                break
            kounter = float('inf')
        path = LineString(route)
    #     plot_route(route=path, path=f"./tests_{datetime_string()}/slides/route_{kounter:08d}.png")
    # make_moving_picture_show(
    #     f"./tests_{datetime_string()}/slides/",
    #     f"./tests_{datetime_string()}/", "route_as_movie"
    # )
    return route


def route_nearest_insertion(waypoints, start_min_arc=True, start_at=None, unknot=True,
                            kounter_limit="auto"):
    if kounter_limit is None:
        kounter_limit = float('inf')
    if kounter_limit == 'auto':
        kounter_limit = len(waypoints) * len(waypoints) // 4
    idx_start_at = None
    if start_at is not None:
        waypoints = set(waypoints)
        waypoints.add(start_at)
    waypoints = sorted(sorted(list(waypoints), key=lambda x: x[0]), key=lambda x: x[1])
    if len(waypoints) <= 1:
        return waypoints, 0
    if start_at is not None:
        idx_start_at = waypoints.index(start_at)
    distance_matrix = scipy.spatial.distance.squareform(scipy.spatial.distance.pdist(waypoints))
    tour = construct_path_nearest_insertion_heuristic(distance_matrix,
                                                      start_min_arc=start_min_arc,
                                                      start_at=idx_start_at)
    route = [waypoints[idx] for idx in tour]
    if unknot:
        unnkot(route, kounter_limit)
    dist = sum(euclidean(p1, p2)
               for p1, p2 in
               zip(route, route[1:]))
    return route, dist


def construct_path_nearest_insertion_heuristic(dist_matrix, start_min_arc, start_at=None):
    p_bar = tqdm(total=len(dist_matrix), position=0, leave=False, desc=f"Routing...")
    default_dist_matrix = copy.deepcopy(dist_matrix)
    D_ijk = namedtuple("D_ijk", ["i", "j", "k", "val"])
    n_cities = len(default_dist_matrix)
    if start_at is None:
        if start_min_arc:
            for i in range(len(dist_matrix)):
                dist_matrix = _set_dist_mat_to(i, i, dist_matrix, val=float('inf'))
            desired_val = dist_matrix.min()
        else:
            desired_val = dist_matrix.max()
            for i in range(len(dist_matrix)):
                dist_matrix = _set_dist_mat_to(i, i, dist_matrix, val=float('inf'))
        __is, __js = np.where(desired_val == dist_matrix)
        __i, __j = int(__is[0]), int(__js[0])
        tour = [-999] + [__i, __j] + [-888]
        fac = 0
    else:
        if start_min_arc:
            for i in range(len(dist_matrix)):
                dist_matrix = _set_dist_mat_to(i, i, dist_matrix, val=float('inf'))
            desired_val = dist_matrix[start_at,].min()
        else:
            desired_val = dist_matrix[start_at,].max()
            for i in range(len(dist_matrix)):
                dist_matrix = _set_dist_mat_to(i, i, dist_matrix, val=float('inf'))
        __j = int(np.where(desired_val == dist_matrix[start_at,])[0][0])
        __i = start_at
        tour = [__i, __j] + [-888]
        assert tour[0] == start_at and start_at not in tour[1:], \
            f"tour[0] == start_at {bool(tour[0] == start_at)} | start_at not in tour[1:] {bool(start_at not in tour[1:])}"
        fac = 1

    dist_matrix = _set_dist_mat_to(__i, __j, dist_matrix, val=float('inf'))

    while len(tour) < n_cities + 2 - fac:
        waypoint, dist_matrix, _other = _find_next_waypoint_to_insert(dist_matrix, tour)
        change_arc_list = [
            D_ijk(i, j, waypoint, _d_ijk(i, j, waypoint, default_dist_matrix))
            for i, j in zip(tour, tour[1:])
        ]
        change_arc_list.sort(key=lambda __x: __x.val)
        if change_arc_list:
            near_insert = change_arc_list.pop(0)
            while near_insert.k in tour:
                near_insert = change_arc_list.pop(0)
            idx_i = tour.index(near_insert.i)
            tour = tour[:idx_i + 1] + [near_insert.k] + tour[idx_i + 1:]
            for element in tour[1:-1]:
                dist_matrix = _set_dist_mat_to(near_insert.k, element, dist_matrix, val=float('inf'))
        else:
            assert False, "Something Has Gone Wrong Here!"
        p_bar.set_postfix_str(f"{len(tour) - 2}")
        p_bar.update()
    if start_at is not None:
        return tour[0:-1]
    return tour[1:-1]


def _set_dist_mat_to(i, j, dm, val=float('inf')):
    dm[i, j] = val
    dm[j, i] = val
    return dm


def _get_val_from_dist_matrix(_i, _j, _dist_matrix):
    if _i in {-888, -999} or _j in {-888, -999}:
        return 0
    if _i == _j:
        return 0
    return _dist_matrix[_i, _j]


def _d_ijk(_i, _j, _k, _dist_matrix):
    return _get_val_from_dist_matrix(_i, _k, _dist_matrix) + \
           _get_val_from_dist_matrix(_k, _j, _dist_matrix) - \
           _get_val_from_dist_matrix(_i, _j, _dist_matrix)


def _find_next_waypoint_to_insert(_dist_matrix, tour):
    while True:
        min_val = _dist_matrix[tour[1:-1], :].min()
        _is, _js = np.where(min_val == _dist_matrix)
        _i, _j = int(_is[0]), int(_js[0])
        _dist_matrix = _set_dist_mat_to(_i, _j, _dist_matrix, val=float('inf'))
        if _i in tour and not (_j in tour):
            return _j, _dist_matrix, _i
        elif _j in tour and not (_i in tour):
            return _i, _dist_matrix, _j
        elif min_val >= float('inf'):
            assert False
