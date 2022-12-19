import os

from pars.parfile_reader import dump_parfile, parfile_reader


def KILL_SWITCH(kill_file, kill_name, set_val=None):
    if not os.path.exists(kill_file):
        dump_parfile({kill_name: False}, kill_file)
    kill_switch = parfile_reader(kill_file)
    if kill_name not in kill_switch:
        kill_switch[kill_name] = False
        dump_parfile(kill_switch, kill_file)
    if set_val is not None:
        kill_switch[kill_name] = set_val
        dump_parfile(kill_switch, kill_file)
    if kill_switch.get(kill_name, False):
        raise Exception(f"Killed {kill_name} by kill switch")
