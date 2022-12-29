import concurrent.futures
import datetime
import os
import socket
import traceback

from tqdm import tqdm

from pars.parfile_reader import many_parfiles_reader, dump_parfile
from project_archangel import project_archangel
from utilities.kill_switch import KILL_SWITCH
from utilities.telegram_bot import telegram_bot_send_message
from utilities.utilities import datetime_string


def generalizable_test_box(parfile, computer_name, k, *args):
    try:
        KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name=socket.gethostname())
    except:
        traceback.print_exc()
        telegram_bot_send_message(
            f"<pre><b>{computer_name}</b></pre>"
            f"\nKILLED!\n"
            f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        telegram_bot_send_message(
            f"<pre><b>{computer_name}</b></pre>"
            f"\nTRACEBACK :\n"
            f"<pre>{traceback.format_exc()}</pre>")
        assert False
    telegram_bot_send_message(
        f"<pre><b>{computer_name}</b></pre>\n"
        f"Starting! {k:0>6}\n"
        f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        log_file = f"./logs/log_{socket.gethostname()}_{datetime_string()}_{k:0>6}.csv"
        tests_completed_file =f"./datafiles/tests_completed_{k:0>6}.json"
        tests_completed_folder = f"./datafiles/"
        project_archangel(
            parfile=parfile,
            log_file_path=log_file,
            tests_completed_file=tests_completed_file,
            tests_completed_folder=tests_completed_folder,
            skip_complex=True
        )
    except:
        traceback.print_exc()
        telegram_bot_send_message(
            f"<pre><b>{computer_name}</b></pre>"
            f"\nERROR!  {k:0>6}\n"
            f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        telegram_bot_send_message(
            f"<pre><b>{computer_name}</b></pre>"
            f"\nTRACEBACK :\n"
            f"<pre>{traceback.format_exc()}</pre>")
    else:
        telegram_bot_send_message(
            f"<pre><b>{computer_name}</b></pre>\n"
            f"FINISHED SUCCESSFULLY! {k:0>6}\n"
            f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    telegram_bot_send_message(
        f"<pre><b>{computer_name}</b></pre>\n"
        f"Teminated {k:0>6}\n"
        f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def cycle_generalizable_test_box(parfiles_folder, tests_completed_file):
    parfiles = many_parfiles_reader(parfiles_folder)
    if not os.path.exists(tests_completed_file):
        dump_parfile(dict(), tests_completed_file)
    for parfile in parfiles:
        generalizable_test_box(
            parfile,
            socket.gethostname(),
            tests_completed_file, 0
        )


def cycle_generalizable_test_box_mp(parfiles_folder, tests_completed_file):
    parfiles = many_parfiles_reader(parfiles_folder)
    KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name=socket.gethostname())
    if not os.path.exists(tests_completed_file):
        dump_parfile(dict(), tests_completed_file)
    arg_list = [(
        parfile,
        socket.gethostname(),
        i
    ) for i, parfile in enumerate(tqdm(parfiles))]
    with concurrent.futures.ProcessPoolExecutor() as PPE:
        r = PPE.map(generalizable_test_box_wrapper, arg_list)
        for _ in tqdm(r, total=len(arg_list), desc="OUTER WRAPPER"):
            pass


def generalizable_test_box_wrapper(args):
    generalizable_test_box(*args)


if __name__ == '__main__':
    cycle_generalizable_test_box_mp(
        parfiles_folder="./pars/testing_folder_experiments_1/",
        tests_completed_file="./datafiles/tests_completed.json"
    )
