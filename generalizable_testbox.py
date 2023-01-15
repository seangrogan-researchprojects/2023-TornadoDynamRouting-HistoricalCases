import concurrent.futures
import datetime
import os
import socket
import traceback
from concurrent.futures import as_completed

from tqdm import tqdm

from pars.parfile_reader import many_parfiles_reader, dump_parfile
from project_archangel import project_archangel
from tests_completed_counter import tests_completed_counter_telegram_message
from utilities.kill_switch import KILL_SWITCH
from utilities.telegram_bot import telegram_bot_send_message
from utilities.utilities import datetime_string


def generalizable_test_box(parfile, computer_name, k, sklim, skcom, *args):
    try:
        KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name=F"LOCAL_{socket.gethostname()}")
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
        tests_completed_file = f"./datafiles/tests_completed_{k:0>6}.json"
        tests_completed_folder = f"./datafiles/"
        project_archangel(parfile=parfile, log_file_path=log_file,
                          tests_completed_file=tests_completed_file,
                          tests_completed_folder=tests_completed_folder,
                          skip_complex=skcom,
                          skip_limit=sklim)
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
    parfile_folder = os.path.dirname(parfile)
    tests_completed_counter_telegram_message(
        f"./datafiles/",
        parfile_folder
    )
    KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name=F"LOCAL_{socket.gethostname()}")


def cycle_generalizable_test_box(parfiles_folder, tests_completed_file, sklim):
    parfiles = many_parfiles_reader(parfiles_folder)
    if not os.path.exists(tests_completed_file):
        dump_parfile(dict(), tests_completed_file)
    for parfile in parfiles:
        generalizable_test_box(
            parfile,
            socket.gethostname(),
            tests_completed_file, 0, sklim
        )


def cycle_generalizable_test_box_mp(parfiles_folder, tests_completed_file, sklim, skcom, max_workers=None):
    parfiles = sorted(many_parfiles_reader(parfiles_folder))
    KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name=socket.gethostname())
    if not os.path.exists(tests_completed_file):
        dump_parfile(dict(), tests_completed_file)
    arg_list = [(
        parfile,
        socket.gethostname(),
        i, sklim, skcom
    ) for i, parfile in enumerate(tqdm(parfiles))]
    # generalizable_test_box(
    #     parfile="./pars/testing_folder_experiments_3/pars_default.json",
    #     computer_name=socket.gethostname(),
    #     k=0,
    #     sklim=sklim,
    #     skcom=skcom
    # )
    if 0 < max_workers < 1:
        max_workers = max(1, min(int(round(max_workers * os.cpu_count())), os.cpu_count() - 1))
        print(f"max_workers : {max_workers}")
    elif max_workers is not None:
        max_workers = max(1, min(max_workers, os.cpu_count()))
        print(f"max_workers : {max_workers}")
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as PPE:
        r = [PPE.submit(generalizable_test_box_wrapper, args=arg) for arg in arg_list]
        for _ in tqdm(as_completed(r), total=len(arg_list), desc="OUTER WRAPPER"):
            pass
    telegram_bot_send_message(
        f"<pre><b>{socket.gethostname()}</b></pre>\n"
        f"Teminated\n"
        f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def generalizable_test_box_wrapper(args):
    generalizable_test_box(*args)


if __name__ == '__main__':
    KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name=socket.gethostname(), set_val=False)
    KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name="GLOBAL1", set_val=False)
    KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name=F"LOCAL_{socket.gethostname()}", set_val=False)
    sklims = [5000, False]
    skcoms = [True, False]
    max_workers = 99
    sklim, skcom = False, False

    KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name="GLOBAL1", set_val=False)
    for parfiles_folder in [
        "./pars/testing_folder_experiments_3/",
        "./pars/testing_folder_experiments_4/",
        "./pars/testing_folder_experiments_5/"
    ]:
        KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name="GLOBAL1", set_val=False)
        telegram_bot_send_message(
            f"<pre><b>{socket.gethostname()}</b></pre>\n"
            f"<pre>"
            f"sklim = {sklim}\n"
            f"skcom = {skcom}\n"
            f"foldr = {parfiles_folder}\n"
            f"</pre>"
            f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        cycle_generalizable_test_box_mp(
            parfiles_folder="./pars/testing_folder_experiments_4/",
            tests_completed_file="./datafiles/tests_completed.json",
            sklim=sklim,
            skcom=skcom,
            max_workers=max_workers
        )
        KILL_SWITCH(kill_file="./kill-switch/kill-switch.json", kill_name="GLOBAL1")
