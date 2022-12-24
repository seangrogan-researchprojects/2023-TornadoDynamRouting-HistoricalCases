import math

from tqdm import tqdm

from utilities.utilities import my_round
from waypoint_creators.random_steiner_zone import random_steiner_zone


def create_waypoints(pars, poi, r_scan, method):
    if method in {'auto'}:
        methods = ['rec', 'hex']
        data = []
        for m in methods:
            data.append((m, create_waypoints(pars, poi, r_scan, m)))
        data.sort(key=lambda x: len(x[1]))
        return data[0][1]
    elif method in {'rec', 'rectangle', 'rectangular'}:
        waypoints = rectangular(pars, poi, r_scan)
    elif method in {'hex', 'hexagonal', 'hexagon'}:
        waypoints = hexagon_pattern(pars, poi, r_scan)
    elif method in {'random_steiner', 'rsz'}:
        waypoints = random_steiner_zone(poi, pars, False)
    else:
        raise NotImplementedError(f"Method {method} not implemented")
    return waypoints


def rectangular(pars, poi, r_scan):
    rec_dist = int(math.sqrt(2) * r_scan)
    waypoints = list(set(round_point(pt, rec_dist)
                         for pt in tqdm(poi, desc="Rectangular")))
    return waypoints


def round_point(point, scanning_radius):
    sr = int(scanning_radius * math.sqrt(2))
    x, y = point
    _x, _y = my_round(x, precision=0, base=sr), my_round(y, precision=0, base=sr)
    new_point = (_x, _y)
    return new_point


def hexagon_pattern(pars, points, r_scan, flat_top=True):
    waypoints = _generate_pattern(
        scanning_rad=r_scan, flat_top=flat_top, points=points
    )
    return waypoints


def is_even(x):
    return x % 2 == 0


def make_point(i, j, R, r):
    i_new = my_round(i, 0, 2 * R)
    if is_even(i_new / (2 * R)):
        j_new = my_round(j, 0, 2 * r)
    else:
        j_new = round(my_round(j, 0, 2 * r) + r)
    return i_new, j_new


def _generate_pattern(scanning_rad, points, flat_top):
    R, r = scanning_rad, math.sqrt(3) * scanning_rad / 2
    waypoints = set()
    if flat_top:
        print('\tGenerating Flat Top Hex Pattern')
        for e, n in points:
            waypoints.add(make_point(e, n, R, r))
    else:
        print('\tGenerating Pointy Top Hex Pattern')
        for e, n in points:
            waypoints.add(make_point(n, e, R, r)[::-1])  # need to reverse the tuple
    return waypoints
