import json

from project_archangel import read_tests_completed_files


def tests_completed_counter(folder):
    data = read_tests_completed_files(folder)
    print (len (data))
    print(max(len(k) for k in data.values()))


if __name__ == '__main__':
    tests_completed_counter(f"./datafiles/")