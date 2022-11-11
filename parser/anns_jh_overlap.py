import os
import sys
import csv
import traceback
import pdb
from multiprocessing import Pool
import numpy as np
import pandas as pd
from math import log
from collections import Counter
from functools import reduce
from operator import add

# usage "python anns_jh_overlap.py [log directory] [# of the thread] [query depth] [# of the NDP device] [OPTION]"

DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]
THREAD_NUM = int(sys.argv[2])
QUERY_DEPTH = int(sys.argv[3])
NDP_NUM = int(sys.argv[4])
OPTION = int(sys.argv[5])

FILE = 'debug.log'
POSTFIX = "-OVERLAP"
HOST_DEV_ID = 100
INITIAL_VALUE = -1
HOST = 0
DEVICE = 1
BOTH = 2

HOST_COLUMNS = ["timestamp"]
for i in range(THREAD_NUM):
    for j in range(QUERY_DEPTH):
        HOST_COLUMNS.append(f"({i}, {j})")

DEVICE_COLUMNS = ["timestamp"]
for i in range(THREAD_NUM):
    for j in range(NDP_NUM):
        DEVICE_COLUMNS.append(f"({i}, {j})")

def get_init_list(option):
    _tmp_list = []
    if option:
        columns = DEVICE_COLUMNS
    else:
        columns = HOST_COLUMNS

    for column in columns:
        _tmp_list.append(INITIAL_VALUE)
    return _tmp_list


def get_header(option):
    if option:
        return DEVICE_COLUMNS
    else:
        return HOST_COLUMNS


def set_host_state(stateManager, timestamp, thread_id, query_index, dev_index, point):
    stateManager.set_point(timestamp, thread_id, query_index, point)


def set_device_state(stateManager, timestamp, thread_id, query_index, dev_index, point):
    stateManager.set_point(timestamp, thread_id, dev_index, point)


class StateManager():
    def __init__(self, thread_num, query_depth, csv_writer, option):
        self.thread_num = thread_num
        self.query_depth = query_depth
        self.csv_writer = csv_writer
        self.states = get_init_list(option)

        self.csv_writer.writerow(get_header(option))

    def set_point(self, timestamp, thread_id, query_index, point):
        self.states[0] = timestamp
        self.states[thread_id * self.query_depth + query_index + 1] = point
        self.csv_writer.writerow(self.states)


# point
SET_START = 0
QUERY_SET = (SET_START + 1)
EP_SET = (QUERY_SET + 1)
RANDOM_START = (EP_SET + 1)
DISTANCE_START = (RANDOM_START + 1)
SEND_DOORBELL = (DISTANCE_START + 1)
RECV_DOORBELL = (SEND_DOORBELL + 1)
RECV_SQ = (RECV_DOORBELL + 1)
GET_QUERY_VECTOR_START = (RECV_SQ + 1)
COMPUTATION_START = GET_QUERY_VECTOR_START+1
COMPUTATION_END = (COMPUTATION_START + 1)
CQ_DMA_END = (COMPUTATION_END + 1)
POLLING_END = (CQ_DMA_END + 1)
DISTANCE_END = (POLLING_END + 1)
UPDATE_END = (DISTANCE_END + 1)
TRAVERSE_END = (UPDATE_END + 1)
SET_END = (TRAVERSE_END + 1)


DO_OR_NOT = 0
CALLBACK = 1
POINTS = [
    [HOST, set_host_state],         # SET_START
    [HOST, set_host_state],         # QUERY_SET
    [INITIAL_VALUE, None],          # EP_SET
    [INITIAL_VALUE, None],          # RANDOM_START
    [HOST, set_host_state],         # DISTANCE_START
    [DEVICE, set_device_state],     # SEND_DOORBELL
    [DEVICE, set_device_state],     # RECV_DOORBELL
    [DEVICE, set_device_state],     # RECV_SQ
    [DEVICE, set_device_state],     # GET_QUERY_VECTOR_START
    [DEVICE, set_device_state],     # COMPUTATION_START
    [DEVICE, set_device_state],     # COMPUTATION_END
    [DEVICE, set_device_state],     # CQ_DMA_END
    [INITIAL_VALUE, None],          # POLLING_END
    [HOST, set_host_state],         # DISTANCE_END
    [HOST, set_host_state],         # UPDATE_END
    [HOST, set_host_state],         # TRAVERSE_END
    [HOST, set_host_state],         # SET_END
]


# global list
row_list = []
out_row_list = []

def parsing(file_full_name):
    path = file_full_name[0]
    file = file_full_name[1]
    if OPTION:
        option = '-DEVICE'
    else:
        option = '-HOST'
    output = path.split('/')[-1] + option + POSTFIX

    print(f'{path}/{file}')
    f = open(f'{path}/{file}')
    # csv_f = open(f'{DIRECTORY}/{output}.csv', 'w', newline='')
    csv_f = open(f'./{output}.csv', 'w', newline='')
    wr = csv.writer(csv_f)
    state_manager = StateManager(THREAD_NUM, QUERY_DEPTH, wr, OPTION)

    lines = f.read().splitlines()
    for line in lines:
        row = line.split(': ')
        timestamp = int(row[0])
        point = int(row[-1])
        dev_index = int(row[-2])
        query_index = int(row[-3])
        thread_id = int(row[-4])

        if POINTS[point][DO_OR_NOT] != OPTION:
            continue

        POINTS[point][CALLBACK](state_manager, timestamp, thread_id, query_index, dev_index, point)

    print(output)
    csv_f.close()
    f.close()

if __name__ == '__main__':
    # pool input
    file_full_names = []
    for (path, dir, files) in os.walk(DIRECTORY):
        for file in files:
            if file != FILE:
                continue
            file_full_names.append((path, file))

    # multiprocessing
    with Pool(12) as p:
        p.map(parsing, file_full_names)