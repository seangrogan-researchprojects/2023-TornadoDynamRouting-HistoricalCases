import concurrent.futures
import datetime
import os
import socket
import traceback

from tqdm import tqdm

from pars.parfile_reader import many_parfiles_reader, dump_parfile
from project_archangel import project_archangel
from utilities.telegram_bot import telegram_bot_send_message


def generalizable_test_box(parfile, computer_name, tests_completed_file, *args):
    telegram_bot_send_message(
        f"<pre><b>{computer_name}</b></pre>\n"
        f"Starting!\n"
        f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        project_archangel(parfile, tests_completed_file)
    except:
        traceback.print_exc()
        telegram_bot_send_message(
            f"<pre><b>{computer_name}</b></pre>"
            f"\nERROR!\n"
            f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        telegram_bot_send_message(
            f"<pre><b>{computer_name}</b></pre>"
            f"\nTRACEBACK :\n"
            f"<pre>{traceback.format_exc()}</pre>")
    else:
        telegram_bot_send_message(
            f"<pre><b>{computer_name}</b></pre>\n"
            f"FINISHED SUCCESSFULLY!\n"
            f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    telegram_bot_send_message(
        f"<pre><b>{computer_name}</b></pre>\n"
        f"Teminated\n"
        f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def cycle_generalizable_test_box(parfiles_folder, tests_completed_file):
    parfiles = many_parfiles_reader(parfiles_folder)
    if not os.path.exists(tests_completed_file):
        dump_parfile(dict(), tests_completed_file)
    for parfile in parfiles:
        generalizable_test_box(
            parfile,
            socket.gethostname(),
            tests_completed_file
        )


def cycle_generalizable_test_box_mp(parfiles_folder, tests_completed_file):
    parfiles = many_parfiles_reader(parfiles_folder)
    if not os.path.exists(tests_completed_file):
        dump_parfile(dict(), tests_completed_file)
    arg_list = [(
        parfile,
        socket.gethostname(),
        tests_completed_file
    ) for parfile in tqdm(parfiles)]
    with concurrent.futures.ProcessPoolExecutor() as PPE:
        r = PPE.map(generalizable_test_box_wrapper, arg_list)
        for _ in tqdm(r):
            pass


def generalizable_test_box_wrapper(args):
    generalizable_test_box(*args)


if __name__ == '__main__':
    cycle_generalizable_test_box_mp(
        parfiles_folder="./pars/testing_folder_experiments_1/",
        tests_completed_file="./datafiles/tests_completed.json"
    )
