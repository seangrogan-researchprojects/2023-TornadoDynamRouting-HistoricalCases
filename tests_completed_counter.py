import datetime
import json
import socket
from time import sleep

from pars.parfile_reader import many_parfiles_reader
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
    completed_counter = [1 for k in data.values() if len(k) >= max_tests]
    telegram_bot_send_message(
        f"<pre><b>{socket.gethostname()}</b></pre>"
        f"\nTests Completed Data:\n<pre>"
        f"Tests Attempted : {len(data)}\n"
        f"Tests in Folder : {len(parfiles)}\n"
        f"Tests Attempted : {int(len(data) * 1000 / len(parfiles)) / 10}%\n"
        f"Tests Completed : {int(sum(completed_counter) * 1000 / len(parfiles)) / 10}%\n</pre>"
        f"At {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    tests_completed_counter_telegram_message(f"./datafiles/", "./pars/testing_folder_experiments_1")
    for i in range(48):
        sleep(60*60)
        tests_completed_counter_telegram_message(f"./datafiles/", "./pars/testing_folder_experiments_1")

