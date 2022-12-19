import hashlib
import pickle

from pars.parfile_reader import parfile_reader
from utilities.utilities import automkdir, json_writer


def read_pickle(pickle_file_to_try_to_load):
    print(f"Trying to load pickle file {pickle_file_to_try_to_load}")
    try:
        data = pickle.load(open(pickle_file_to_try_to_load, "rb"))
        print(f" Loaded file {pickle_file_to_try_to_load}")
        return data
    except:
        print(f" Failed to load file {pickle_file_to_try_to_load}")
        return None


def write_pickle(filename, data):
    print(f"Dumping Picklefile {filename}")
    automkdir(filename)
    pickle.dump(data, open(filename, "wb"))


def pickle_dumper(filename, data, key, pickleparfile):
    print(f"Dumping Picklefile {filename}")
    pickles = parfile_reader(pickleparfile)
    automkdir(filename)
    pickle.dump(data, open(filename, "wb"))
    pickles[key] = filename
    json_writer(pickles, pickleparfile)


def hash_something_for_filename(data):
    hashed = hashlib.sha256(str(data).encode('utf-8')).hexdigest()
    return hashed
