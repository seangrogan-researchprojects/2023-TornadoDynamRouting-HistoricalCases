import math
import random
from collections import Counter

import pandas as pd
from great_circle_calculator import great_circle_calculator
from tqdm import tqdm

from utilities.pickles_io import write_symmetric_influence_matrix, read_symmetric_influence_matrix, \
    read_data_driven_influence_matrix, write_data_driven_influence_matrix
from utilities.plotter_utilities import plotter_utilities_mp, plot_influence_matrix
from utilities.utilities import datetime_string, my_round


def create_data_driven_influence_matrix(waypoints, dist_matrix, max_influence, min_influence=0,
                                        tornado_data_file=None, mag_limit=None, bin_width=None, pars=None):
    # try:
    #     influence_matrix = read_data_driven_influence_matrix(waypoints, tornado_data_file, pars)
    #     print(f"Created Data Driven Influence Matrix from pickle!")
    #     return influence_matrix
    # except:
    #     pass
    tornado_data = read_and_process_tornado_file(
        tornado_data_file,
        mag_limit=mag_limit
    )
    bins = create_bins(tornado_data, bin_width=bin_width)
    influence_function = DataDrivenInfluenceFunctions(bins, bin_width)
    influence_matrix = {
        wp1: {wp2:
                  influence_function.linear(wp1, wp2, dist_matrix.at[wp1, wp2], max_influence, min_influence) for wp2 in
              waypoints}
        for idx, wp1 in enumerate(tqdm(waypoints, desc="Building Data-Driven Influence Matrix"))}
    influence_matrix = pd.DataFrame(influence_matrix, index=waypoints, columns=waypoints)
    # influence_matrix = pd.DataFrame(index=waypoints, columns=waypoints)
    # for idx, wp1 in enumerate(tqdm(waypoints, desc="Building Influence Matrix")):
    #     for wp2 in waypoints:
    #         influence_matrix.at[wp1, wp2] = influence_function.linear(
    #             wp1, wp2,
    #             dist_matrix.at[wp1, wp2], max_influence, min_influence
    #         )
    # try:
    #     write_data_driven_influence_matrix(waypoints, influence_matrix, tornado_data_file, pars)
    # except:
    #     pass
    return influence_matrix


def create_symmetric_influence_matrix(waypoints, dist_matrix, max_influence, min_influence=0, pars=None, *kwargs):
    # try:
    #     influence_matrix = read_symmetric_influence_matrix(waypoints, pars)
    #     print(f"Created Symmetric Influence Matrix from pickle!")
    #     return influence_matrix
    # except:
    #     pass
    influence_matrix = {
        wp1: {wp2:
                  InfluenceFunctions.linear(dist_matrix.at[wp1, wp2], max_influence, min_influence) for wp2 in waypoints}
        for idx, wp1 in enumerate(tqdm(waypoints, desc="Building Symmetric Influence Matrix"))}
    influence_matrix = pd.DataFrame(influence_matrix, index=waypoints, columns=waypoints)
    # influence_matrix = pd.DataFrame(index=waypoints, columns=waypoints)
    # for idx, wp1 in enumerate(tqdm(waypoints, desc="Building Influence Matrix")):
    #     for wp2 in waypoints:
    #         influence_matrix.at[wp1, wp2] = InfluenceFunctions.linear(
    #             dist_matrix.at[wp1, wp2], max_influence, min_influence)
    # try:
    #     write_symmetric_influence_matrix(waypoints, influence_matrix, pars)
    # except:
    #     pass
    return influence_matrix


def plot_influence_matrix_helper(waypoints, influence_matrix, n_plots,
                                 BASE_OUTPUT_FOLDER, matrix_type):
    plotter_utilities_mp(plot_influence_matrix, kwargs=dict(
        influence_matrix=influence_matrix,
        path=f"{BASE_OUTPUT_FOLDER}/plots/influence_matrix_samples_{matrix_type}/influence_matrix_center.png",
        zeros_black=True
    ))
    if n_plots == 0:
        return None
    wps = random.sample(waypoints, n_plots)
    for wp in tqdm(wps):
        plotter_utilities_mp(plot_influence_matrix, kwargs=dict(
            influence_matrix=influence_matrix,
            path=f"{BASE_OUTPUT_FOLDER}/plots/influence_matrix_samples_{matrix_type}/influence_matrix_{wp}.png",
            target=wp, zeros_black=True
        ))


class InfluenceFunctions:
    @staticmethod
    def log(d, max_range, min_range=0):
        if d > max_range:
            return 0
        if d <= min_range:
            return 1
        _s = math.log(-1 * (d - min_range) + (max_range + 1), max_range)
        return max(min(_s, 1), 0)

    @staticmethod
    def linear(d, max_range, min_range=0):
        if d > max_range:
            return 0
        if d <= min_range:
            return 1
        _s = 1 - (d - min_range) / max_range
        return max(min(_s, 1), 0)

    @staticmethod
    def one_over_e_to_the_x(d, max_range, min_range=0):
        if d > max_range:
            return 0
        if d <= min_range:
            return 1
        _s = 1 / math.exp((d - min_range) / max_range)
        return max(min(_s, 1), 0)


class DataDrivenInfluenceFunctions:
    def __init__(self, bins, bin_width):
        self.bins = bins
        self.bin_width = bin_width
        directions, counts = zip(*bins.items())
        self.bin_norms = {k: (v / max(counts)) for k, v in bins.items()}

    # @staticmethod
    def get_binned_degrees_between_points(self, p1, p2):
        if p1 == p2:
            return 0
        p0 = (p1[0], p1[1] + 10)
        angle = math.degrees(math.atan2(p0[1] - p1[1], p0[0] - p1[0]) - math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
        while angle < 0:
            angle = angle + 180
        while angle > 180:
            angle = angle - 180
        angle = my_round(angle, base=self.bin_width)
        return angle

    def log(self, p1, p2, d, max_range, min_range=0):
        min_range, max_range = self.get_modifiers(min_range, max_range, p1, p2)
        if d > max_range:
            return 0
        if d <= min_range:
            return 1
        _s = math.log(-1 * (d - min_range) + (max_range + 1), max_range)
        return max(min(_s, 1), 0)

    def linear(self, p1, p2, d, max_range, min_range=0):
        min_range, max_range = self.get_modifiers(min_range, max_range, p1, p2)
        if d > max_range:
            return 0
        if d <= min_range:
            return 1
        _s = 1 - (d - min_range) / max_range
        return max(min(_s, 1), 0)

    def one_over_e_to_the_x(self, p1, p2, d, max_range, min_range=0):
        min_range, max_range = self.get_modifiers(min_range, max_range, p1, p2)
        if d > max_range:
            return 0
        if d <= min_range:
            return 1
        _s = 1 / math.exp((d - min_range) / max_range)
        return max(min(_s, 1), 0)

    def get_modifiers(self, min_range, max_range, p1, p2):
        angle = self.get_binned_degrees_between_points(p1, p2)
        min_range = min_range * (1 + self.bin_norms.get(angle, 0))
        max_range = max_range * (1 + self.bin_norms.get(angle, 0))
        return min_range, max_range


def read_and_process_tornado_file(
        tornado_data_file,
        mag_limit=1
):
    tornado_track_file = pd.read_csv(tornado_data_file)
    # print(len(tornado_track_file))
    if mag_limit is not None:
        tornado_track_file = tornado_track_file[tornado_track_file["mag"] >= mag_limit]
        # print(len(tornado_track_file))
    tornado_track_file = tornado_track_file[tornado_track_file["elat"] != 0]
    # print(len(tornado_track_file))
    tornado_track_file = tornado_track_file[
        (tornado_track_file["elat"] != tornado_track_file["slat"]) &
        (tornado_track_file["elon"] != tornado_track_file["slon"])
        ]
    # print(len(tornado_track_file))
    for eps in [0.1, 0.01, 0.001, 0.0001]:
        tornado_track_file = tornado_track_file[
            (tornado_track_file["elat"] != (tornado_track_file["slat"] + eps)) &
            (tornado_track_file["elon"] != (tornado_track_file["slon"] + eps))
            ]
        # print(len(tornado_track_file))
        tornado_track_file = tornado_track_file[
            (tornado_track_file["elat"] != (tornado_track_file["slat"] - eps)) &
            (tornado_track_file["elon"] != (tornado_track_file["slon"] - eps))
            ]
        # print(len(tornado_track_file))

    tornado_track_file['direction'] = tornado_track_file.apply(
        lambda row:
        round(great_circle_calculator.bearing_at_p1(
            (row['slon'], row['slat']),
            (row['elon'], row['elat'])
        )), axis=1
    )
    tornado_track_file['direction_radians'] = tornado_track_file.apply(
        lambda row:
        math.radians(great_circle_calculator.bearing_at_p1(
            (row['slon'], row['slat']),
            (row['elon'], row['elat'])
        )), axis=1
    )
    return tornado_track_file


def create_bins(tornado_track_file, bin_width=5):
    def reformat_directions_1(_d):
        if _d >= 0:
            return _d
        return 180 + _d

    def reformat_directions_2(_d, _bin_width):
        return my_round(_d, base=_bin_width)

    directions = tornado_track_file['direction'].to_list()
    modified_directions = [reformat_directions_2(reformat_directions_1(d), bin_width) for d in directions]

    c = Counter(modified_directions)
    bins_count = list(c.items())
    bins_count.sort()
    bins = dict(bins_count)
    return bins
