import itertools
import os
from copy import deepcopy

from pars.parfile_reader import dump_parfile, parfile_reader
from utilities.file_movers import open_folder


def parfile_creators(base_folder, filename, **kwargs):
    default_pars = parfile_reader(f"par0.json")
    newparfile = deepcopy(default_pars)
    for key, value in kwargs.items():
        if value is None:
            continue
        newparfile[key] = value
    dump_parfile(
        pars=newparfile,
        output_parfile=f"{base_folder}/{filename}"
    )


def alldiff(elements):
    step1 = [k for k, v in elements]
    step2 = set(step1)
    return len(step1) == len(step2)


if __name__ == '__main__':
    outfolder = f"testing_folder_experiments_1"
    alt_pars = {
        "min_score_to_consider": [0, 0.1, 0.2],
        "influence_matrix_type": ["symmetric", "data-driven", "symmetric-first", "data-driven-first"],
        "init_route": [True, False],
        "routing_mode": ["order_scores"],
        "max_influence": [10000, 20000],
        "r_scan": [2500],
        "score_damaged": [10, 20]
    }
    data = []
    for par, values in alt_pars.items():
        for value in values:
            data.append((par, value))
    ParameterCombinations = [
        elements for elements in itertools.combinations(data, len(alt_pars)) if alldiff(elements)
    ]
    for pars in ParameterCombinations:
        name = ""
        for n, v in pars:
            if v is None:
                continue
            n_new = n.replace("_", " ")
            n_new = n_new.title()
            n_new = n_new.replace(" ", "")
            name += f"{n_new}-{v}_"
        if name == "":
            continue
        name = name[:-1]
        pars_to_overwrite = dict(pars)
        pars_to_overwrite["case_name"] = name
        parfile_creators(outfolder, f"pars-{name}.json", **pars_to_overwrite)
    parfile_creators(outfolder, f"pars_default.json")
    open_folder(outfolder)
