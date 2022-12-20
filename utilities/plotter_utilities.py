from multiprocessing import Process

import matplotlib.pyplot as plt
from shapely.geometry import MultiPolygon

from utilities.utilities import automkdir, euclidean, datetime_string

GLOBAL_OVERRIDES = dict(
    dpi=300,
    bbox_inches="tight"
)


def plotter_utilities_mp(function, args=(), kwargs={}, mp=True):
    if not mp:
        function(*args, **kwargs)
    else:
        p = Process(target=function, args=args, kwargs=kwargs)
        p.start()


def plot_case_info(other_random_case_data, random_seed, pars, BASE_OUTPUT_FOLDER):
    waypoints, sbw, sbw_vertices, tornado_init, \
    tornado_direction, tornado_length, tornado_width, \
    damage_polygon, minimum_hamiltonian_path, minimum_hamiltonian_path_distance = other_random_case_data

    plot_with_polygon_case(
        **dict(
            waypoints=waypoints,
            sbw=sbw,
            sbw_verts=sbw_vertices,
            damage_poly=damage_polygon,
            tornado_point=tornado_init,
            show=False,
            title=f"Case {random_seed} w/Route {minimum_hamiltonian_path_distance}",
            path=f"{BASE_OUTPUT_FOLDER}/all_info_case_{random_seed}_with_route.png",
            route=minimum_hamiltonian_path
        )
    )
    plot_with_polygon_case(
        **dict(
            waypoints=waypoints,
            sbw=sbw,
            sbw_verts=sbw_vertices,
            damage_poly=damage_polygon,
            tornado_point=tornado_init,
            show=False,
            title=f"Case {random_seed}",
            path=f"{BASE_OUTPUT_FOLDER}/all_info_case_{random_seed}.png"
        )
    )


def plot_influence_matrix(influence_matrix, path=None, show=False, *,
                          target=None, get_close_to_target=True, zeros_black=False):
    """
    This plots the "Influence Matrix" and the influence of
    :param influence_matrix:
    :param target: if none, will get waypoint closest to center
    :param get_close_to_target: if true it will find the waypoint closest to the target point, otherwise throw an error
    """
    # print(f"Plotting Influence Matrix {path}")
    fig1, ax = plt.subplots()
    ax.set_aspect("equal")
    waypoints = influence_matrix.index.to_list()
    x, y = zip(*waypoints)
    if target is None:
        target = ((max(x) - min(x)) // 2, (max(y) - min(y)) // 2)
        get_close_to_target = True
    if get_close_to_target and bool(target):
        closest_to_target = {wp: euclidean(wp, (target[0], target[1])) for wp in waypoints}
        target = min(closest_to_target, key=closest_to_target.get)
        scores = influence_matrix[target].to_list()
    else:
        scores = influence_matrix[target].to_list()

    if zeros_black:
        all_data = list(zip(x, y, scores))

        data = [ele for ele in all_data if ele[2] <= 0]
        x, y, scores = zip(*data)
        plt.scatter(x, y, c="black")

        data = [ele for ele in all_data if ele[2] > 0]
        if data:
            x, y, scores = zip(*data)
            plt.scatter(x, y, c=scores, cmap="autumn", vmin=0, vmax=1)
    else:
        plt.scatter(x, y, c=scores, cmap="autumn", vmin=0, vmax=1)
    plt.scatter(target[0], target[1], c='blue')
    # plt.set_aspect("equal")
    if bool(path):
        automkdir(path)
        global GLOBAL_OVERRIDES
        plt.savefig(path, **GLOBAL_OVERRIDES)
    if bool(show):
        plt.show()
    plt.close()
    # print(f"Done Plotting Influence Matrix {path}")


def plot_with_polygon_case(waypoints=None, sbw=None, sbw_verts=None,
                           damage_poly=None, tornado_point=None, bounds=None,
                           torn_path=None,
                           show=False, title=None, path=None, route=None):
    print(f"Plotting Case {path}")
    fig1, ax = plt.subplots()
    ax.set_aspect("equal")
    if bounds:
        lb_x, ub_x, lb_y, ub_y = bounds
        plt.xlim(lb_x, ub_x)
        plt.ylim(lb_y, ub_y)
    if waypoints:
        x, y = zip(*waypoints)
        plt.scatter(x, y)
    if sbw:
        if isinstance(sbw, list):
            for s in sbw:
                if isinstance(s, MultiPolygon):
                    for s2 in list(s.geoms):
                        x, y = s2.exterior.xy
                        plt.plot(x, y, color='gold')
                else:
                    x, y = s.exterior.xy
                    plt.plot(x, y, color='red')
        else:
            x, y = sbw.exterior.xy
            plt.plot(x, y, color='red')
    if sbw_verts:
        x, y = zip(*sbw_verts)
        plt.scatter(x, y, color='red')
    if tornado_point:
        plt.scatter(tornado_point[0], tornado_point[1], color='red', marker='v')
    if torn_path:
        x, y = zip(*torn_path)
        plt.plot(x, y, color='gold')
    if damage_poly:
        if isinstance(damage_poly, list):
            for dp in damage_poly:
                if isinstance(dp, MultiPolygon):
                    for dp2 in list(dp.geoms):
                        x, y = dp2.exterior.xy
                        plt.plot(x, y, color='gold')
                else:
                    x, y = dp.exterior.xy
                    plt.plot(x, y, color='gold')
        elif isinstance(damage_poly, MultiPolygon):
            for dp2 in list(damage_poly.geoms):
                x, y = dp2.exterior.xy
                plt.plot(x, y, color='gold')
        else:
            x, y = damage_poly.exterior.xy
            plt.plot(x, y, color='gold')
    if route:
        x, y = zip(*route)
        plt.plot(x, y, color='blue')
    if title:
        plt.title(title)
    if path:
        automkdir(path)
        global GLOBAL_OVERRIDES
        plt.savefig(path, **GLOBAL_OVERRIDES)
    if show:
        plt.show()
    plt.close()
    print(f"Done Plotting Case {path}")


def plot_route(route, path, lasts=None):
    plt.plot(*route.xy)
    if lasts:
        x, y = zip(*lasts)
        plt.scatter(x, y, cmap="Dark2", c=[1, 2, 3, 4])
    if path:
        automkdir(path)
        global GLOBAL_OVERRIDES
        plt.savefig(path, **GLOBAL_OVERRIDES)
    plt.close()


def plot_route_and_wp_scores(waypoints_data, route_as_visited=None, route_to_visit=None,
                             show=False, title=None, path=None
                             ):
    COLOR_PARAMS = dict(
        route_as_visited_color="red",
        route_to_visit_color="fuchsia",
        scores="viridis"
    )
    fig, ax = plt.subplots()
    ax.set_aspect("equal")
    wpts_x, wpts_y, wpts_score = \
        waypoints_data["_wp_x"].to_list(), waypoints_data["_wp_y"].to_list(), waypoints_data["score"].to_list()
    ax.scatter(wpts_x, wpts_y, c=wpts_score, cmap=COLOR_PARAMS["scores"], vmin=0, vmax=1)

    if route_to_visit:
        to_plt = [route_as_visited[-1]] + route_to_visit[:]
        x, y = zip(*to_plt[:])
        ax.plot(x, y, c=COLOR_PARAMS["route_to_visit_color"])
    if title:
        plt.title(title)
    if route_as_visited:
        x, y = zip(*route_as_visited)
        ax.plot(x, y, c=COLOR_PARAMS["route_as_visited_color"])
        x, y = route_as_visited[-1]
        ax.scatter(x, y, c=COLOR_PARAMS["route_as_visited_color"], marker="2")
    if path:
        automkdir(path)
        global GLOBAL_OVERRIDES
        plt.savefig(path, **GLOBAL_OVERRIDES)
    if show:
        plt.show()
    plt.close()
