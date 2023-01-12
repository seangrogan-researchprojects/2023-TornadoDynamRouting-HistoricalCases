import datetime
import json
import socket
from collections import Counter
from statistics import median, mode
from time import sleep

from pars.parfile_reader import many_parfiles_reader, parfile_reader
from project_archangel import read_tests_completed_files
from utilities.telegram_bot import telegram_bot_send_message


def tests_completed_counter(folder):
    data = read_tests_completed_files(folder)
    print(len(data))
    print(max(len(k) for k in data.values()))


def tests_completed_counter_telegram_message(folder, parfiles_folder):
    data = read_tests_completed_files(folder)
    parfiles = many_parfiles_reader(parfiles_folder)
    max_tests = max(len(k) for k in data.values())
    min_tests = min(len(k) for k in data.values())
    mode_tests = mode(len(k) for k in data.values())
    completed_counter = [1 for k in data.values() if len(k) >= max_tests]
    close_completed_counter = [1 for k in data.values() if len(k) >= (mode_tests*0.995)]
    telegram_bot_send_message(
        f"<pre><b>{socket.gethostname()}</b></pre>"
        f"\nTests Completed Data:\n<pre>"
        f"Tests Attempted : {len(data)}\n"
        f"Tests in Folder : {len(parfiles)}\n"
        f"Tests Attempted : {int(len(data) * 1000 / len(parfiles)) / 10}%\n"
        f"Tests Completed : {int(sum(completed_counter) * 1000 / len(parfiles)) / 10}%\n"
        f"Close Completed : {int(sum(close_completed_counter) * 1000 / len(parfiles)) / 10}%\n</pre>"
        f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def tests_completed_counter_telegram_message_2(folder, parfiles_folder, top_n=5, skip_done=True):
    data = read_tests_completed_files(folder)
    parfiles = many_parfiles_reader(parfiles_folder)
    names = [parfile_reader(parfile)['case_name'] for parfile in parfiles]
    test_counter = sorted([(len(v), k) for k, v in data.items()])
    max_tests = max(len(k) for k in data.values())
    incomplete_counter = sorted([(len(v), k) for k, v in data.items() if len(v) < max_tests])
    v, k = zip(*incomplete_counter)
    counter = Counter(v)
    kounter = 0
    for v, k in reversed(test_counter):
        if skip_done and v>=max_tests:
            kounter += 1
            continue
        if v >= max_tests:
            print("*", end=" ")
        else:
            print(" ", end=" ")
        if k in names:
            print("#", end=" ")
        else:
            print(" ", end=" ")
        print(f"{v: >{len(str(max_tests))}} of {max_tests} : {k}")
    if kounter > 0:
        print(f"  {kounter} par files have reached {max_tests}")
    # incomplete_counter = sorted(incomplete_counter, reverse=True)[:top_n]
    # msg = ""
    # for v, k in incomplete_counter:
    #     msg += f"{v} of {max_tests} : {k}\n"
    # telegram_bot_send_message(
    #     f"<pre><b>{socket.gethostname()}</b></pre>"
    #     f"\nIncomplete Data:\n<pre>"
    #     f"{msg}"
    #     f"</pre>\n"
    #     f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    msg = ""
    for k, v in counter.items():
        msg += f"{k: >4}:{v: >4} of {max_tests}\n"
    telegram_bot_send_message(
        f"<pre><b>{socket.gethostname()}</b></pre>"
        f"\nIncomplete Data:\n<pre>"
        f"{msg}"
        f"</pre>\n"
        f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    folder = f"./datafiles/"
    parfiles_folder1 = "./pars/testing_folder_experiments_3"
    parfiles_folder2 = "./pars/testing_folder_experiments_4"
    tests_completed_counter_telegram_message(folder, parfiles_folder2)
    tests_completed_counter_telegram_message_2(folder, parfiles_folder2)
    for i in range((48*2)):
        # sleep(60 * 10)
        # tests_completed_counter_telegram_message(folder, parfiles_folder1)
        # tests_completed_counter_telegram_message_2(folder, parfiles_folder1)
        sleep(60 * 10)
        tests_completed_counter_telegram_message(folder, parfiles_folder2)
        tests_completed_counter_telegram_message_2(folder, parfiles_folder2)
