import os
import sys
import traceback
import pdb
import re
import numpy as np
import pandas as pd
from math import log
from collections import Counter
from functools import reduce
from operator import add
from multiprocessing import Pool

# directory name: {dataset}_{search-l}_{type}_{# of the shard}
# usage "python anns_host_state_parser.py [log directory] [# of the thread] [query depth] [period]"

OUTLIER_THRESHOLD = 50000000
# OUTLIER_THRESHOLD = 20000000

DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]
THREAD_NUM = int(sys.argv[2])
QUERY_DEPTH = int(sys.argv[3])
PERIOD = int(sys.argv[4])

FILE = 'debug.log'
TERMINAL_FILE = 'system.terminal'
POSTFIX = "-STATE"

COLUMNS = [
    "timestamp",
]
for i in range(THREAD_NUM):
    COLUMNS.append(f'{i} host state')

BUSY = 1
PENDING = 0

def getInitDict():
    _tmp_dict = {}
    for column in COLUMNS:
        _tmp_dict[column] = 0
    return _tmp_dict

MAGIC_WORDS = ['Q']

INITIAL_VALUE = -1

### point ###
# host
SEND_DOORBELL_DONE = 'send_doorbell_done'
POLLING_END_DONE = 'polling_end_done'

INTERESTED_POINTS = [
    SEND_DOORBELL_DONE,
    POLLING_END_DONE
]


class HostStates:
    def __init__(self, num_thread, period, row_list):
        self.num_thread = num_thread
        self.nex_tick = period
        self.period = period
        self.states = getInitDict()
        self.isFirst = True


    def error(self, log_line):
        print(log_line)
        traceback.print_tb()
        exit(1)


    def insert_host_state(self, thread_id, point, timestamp, log_line, row_list):
        if self.isFirst:
            self.states['timestamp'] = timestamp - (timestamp % self.period)
            self.nex_tick = self.states['timestamp'] + self.period
            self.isFirst = False
            return

        if self.nex_tick < timestamp:
            self.states['timestamp'] = self.nex_tick
            row_list.append(self.states)
            self.states = self.states.copy()
            self.nex_tick = self.nex_tick + self.period

            while self.nex_tick < timestamp:
                self.states['timestamp'] = self.nex_tick
                row_list.append(self.states)
                self.states = self.states.copy()
                self.nex_tick = self.nex_tick + self.period

            self.states['timestamp'] = timestamp

        if point == SEND_DOORBELL_DONE:
            self.states[f'{thread_id} host state'] = PENDING
        elif point == POLLING_END_DONE:
            self.states[f'{thread_id} host state'] = BUSY
        else:
            self.error(log_line)

def parsing(file_full_name):
    path = file_full_name[0]
    file = file_full_name[1]

    setting = path.split('/')[-1]
    ndp_num = int(setting.split('_')[-1])

    row_list = []
    output = setting + POSTFIX

    host_states = HostStates(THREAD_NUM, PERIOD, row_list)

    print(f'{path}/{file}')
    f = open(f'{path}/{file}')
    lines = f.read().splitlines()
    for line in lines:
        row = line.split(': ')
        magic_word = row[2]
        if magic_word not in MAGIC_WORDS:
            continue

        tick = int(row[0])
        point = row[-1]
        # dev_index = int(row[-2])
        query_index = int(row[-3])
        thread_id = int(row[-4])

        if point not in INTERESTED_POINTS:
            continue

        host_states.insert_host_state(thread_id, point, tick, line, row_list)

    df = pd.DataFrame(row_list, columns=COLUMNS).fillna(0).astype(int)

    df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
    f.close()
    print(f'{path}/{file} done')


if __name__ == '__main__':
    # pool input
    file_full_names = []
    for (path, dir, files) in os.walk(DIRECTORY):
        for file in files:
            if file != FILE:
                continue
            file_full_names.append((path, file))

    # multiprocessing
    with Pool(1) as p:
        p.map(parsing, file_full_names)
