import json
import os.path
import warnings

from utilities.utilities import automkdir


def parfile_reader(parfile_name):
    try:
        filename, file_extension = os.path.splitext(parfile_name)
        if file_extension not in {'.json'}:
            parfile_name = f"{parfile_name}.json"
            warnings.warn(f"Assuming filename {parfile_name}")
        with open(parfile_name) as f:
            pars = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not read {parfile_name}")
    return pars


def dump_parfile(pars, output_parfile):
    automkdir(output_parfile)
    with open(output_parfile, "w") as f:
        json.dump(pars, f, indent=4)


def many_parfiles_reader(folder_with_parfiles):
    files_list = [
        os.path.join(folder_with_parfiles, file)
        for file in os.listdir(folder_with_parfiles) if file.endswith(".json")
    ]
    return files_list


if __name__ == '__main__':
    print(parfile_reader("par1"))
