import datetime
import json
import os
import random

from tqdm import tqdm


def read_used_seed_file():
    try:
        file = "D:/Users/seang/OneDrive - polymtl.ca/project-archangel-logfiles-EXPERIMENTS/random_seeds_used.json"
        with open(file) as f:
            return json.load(f)
    except:
        return list()


def make_random_seed_list(n_seeds, random_seed=None, skip_first_n_seeds=None):
    _ub = 1_000_000
    used_seeds = read_used_seed_file()
    if n_seeds > _ub // n_seeds:
        _ub = _ub * n_seeds
    fac = 0
    if skip_first_n_seeds is not None:
        seeds = set()
        while len(seeds) < skip_first_n_seeds:
            seeds.add(random.randint(1, _ub))
    if random_seed is not None:
        random.seed(random_seed)
        if skip_first_n_seeds is not None:
            fac -= 1
    seeds = set()
    pbar = tqdm(desc="creating seeds")
    while len(seeds) < n_seeds - fac:
        seed = random.randint(1, _ub)
        if seed not in used_seeds:
            seeds.add(seed)
            pbar.set_postfix_str(f"n_seeds = {len(seeds)}")
        pbar.update()
    seeds = list(seeds)
    if random_seed is not None and skip_first_n_seeds is not None:
        seeds.insert(0, random_seed)
    return list(seeds)


def datetime_string(_dt=datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), current=False):
    if current:
        return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return _dt


def inject_datetime_str(file_path):
    filename, file_extension = os.path.splitext(file_path)
    return f"{filename}_{datetime_string()}{file_extension}"


def json_writer(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def midpoint(p1, p2):
    return tuple((j + i) / 2 for i, j in zip(p1, p2))


def automkdir(filename):
    if bool(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename), exist_ok=True)


def my_round(x, precision=0, base=5):
    """
    :param x: Number to round
    :param precision: rounded to the multiple of 10 to the power minus precision
    :param base: to the nearest 'base'
    :return: rounded value
    """
    return round(base * round(float(x) / base), int(precision))


def euclidean(p1, p2):
    return pow(sum(pow((a - b), 2) for a, b in zip(p1, p2)), 0.5)
