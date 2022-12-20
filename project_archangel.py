import datetime

import pandas as pd
import geopandas as gpd
from tqdm import tqdm

from pars.parfile_reader import parfile_reader
from project_archangel_subfunctions import get_historical_cases_data
from utilities.pickles_io import read_pickle, write_pickle
from utilities.plotter_utilities import plot_with_polygon_case
from utilities.utilities import flatten_a_list, automkdir


def project_archangel(parfile):
    pars = parfile_reader(parfile)
    sbws, damage_polygons, dates = get_historical_cases_data(pars)
    events_by_date = get_events_by_date(pars, damage_polygons, sbws, dates)
    make_minimum_cases(dates, events_by_date, pars)

def make_minimum_cases(dates, events_by_date, pars):
    for date in dates:
        print(f"Plotting Information")
        event_data = events_by_date[date]
        output_loc = f"{pars['shapefile_by_date_location']}/{date}"
        automkdir(f"{output_loc}/sbws_{date}.gpkg")

        plot_with_polygon_case(sbw=event_data['sbws'].geometry.to_list(),
                               damage_poly=event_data['damage'].geometry.to_list(),
                               show=False, title=f"{date} | {len(event_data['sbws'])}",
                               path=f"./plots/{date}.png")
        make_smaller_events(pars, date, event_data)


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
    while len(cases) >0:
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
    for data in data_to_return:
        tornadoes, sbws, tor_ids = data
        tor_id = ":".join(str(t) for t in tor_ids)
        plot_with_polygon_case(sbw=sbws,
                               damage_poly=tornadoes,
                               show=False,
                               title=f"{date} | {tor_id}",
                               path=f"./plots_separated_v2/{date}_{tor_id.replace(':', '-')}.png")
    return data_to_return


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


if __name__ == '__main__':
    project_archangel("./pars/par0.json")
