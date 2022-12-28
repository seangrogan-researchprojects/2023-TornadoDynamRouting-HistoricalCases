import datetime
import os
from time import sleep

from pars.parfile_reader import parfile_reader, dump_parfile


def kill_all(path):
    kill_data = parfile_reader(path)
    kill_data = {k: True for k in kill_data.keys()}
    dump_parfile(kill_data, path)


def kill_all_at(time, path):
    print(f"Kill all activated for {time}")
    while True:
        sleep(60)
        if datetime.datetime.now() > time:
            print(f"Killing all!\nTime {time} reached at {datetime.datetime.now()}")
            kill_all(path)
            return 0


def KILL_SWITCH(f, k, set_val=None):
    if not os.path.exists(f):
        dump_parfile({k: False}, f)
    kill_switch = parfile_reader(f)
    if k not in kill_switch:
        kill_switch[k] = False
        dump_parfile(kill_switch, f)
    if set_val is not None:
        kill_switch[k] = set_val
        dump_parfile(kill_switch, f)
    if kill_switch.get(k, False):
        raise Exception(f"Killed {k} by kill switch")


if __name__ == '__main__':
    # kill_all_at(datetime.datetime(2022, 10, 28, 16, 00), "./kill-switch/kill-switch.json")
    kill_all("./kill-switch/kill-switch.json")
