from pars.parfile_reader import dump_parfile
from project_archangel import read_tests_completed_files

tests_completed_folder = "./datafiles/"
tests_completed_file = "./datafiles/tests_completed.json"
tests_completed = read_tests_completed_files(tests_completed_folder)
dump_parfile(tests_completed, tests_completed_file)
