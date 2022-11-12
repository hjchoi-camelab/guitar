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

# usage "python anns_jh_device_utilization.py [log directory] [# of the thread] [query depth] [# of the NDP device] [# of the NDP units per device]"

DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]
THREAD_NUM = int(sys.argv[2])
QUERY_DEPTH = int(sys.argv[3])
NDP_NUM = int(sys.argv[4])
UNIT_NUM = int(sys.argv[5])

FILE = 'debug.log'
POSTFIX = "-DEVICE-UTILIZATION"
HOST_DEV_ID = 100
INITIAL_VALUE = -1
HOST = 0
DEVICE = 1
BOTH = 2

COLUMNS = ["timestamp"]
for i in range(THREAD_NUM):
    COLUMNS.append(f"{i}")

def get_init_list(option):
    _tmp_list = []
    columns = COLUMNS

    for column in columns:
        _tmp_list.append(0)

    return _tmp_list


def get_header(option):
    return COLUMNS


def set_state(stateManager, timestamp, thread_id, query_index, dev_index, point):
    stateManager.set_point(timestamp, thread_id, dev_index, point)


class StateManager():
    def __init__(self, thread_num, query_depth, csv_writer):
        self.thread_num = thread_num
        self.query_depth = query_depth
        self.csv_writer = csv_writer
        self.states = get_init_list()

        self.csv_writer.writerow(get_header())

    def set_point(self, timestamp, thread_id, dev_index, point):
        update_utilization(thread_id, dev_index, point)
        self.states[0] = timestamp
        self.states[thread_id + 1] = get_utilization(thread_id)
        self.csv_writer.writerow(self.states)


### point ###
# host
SET_START = 'set_start'
QUERY_SET = 'query_set'
DISTANCE_START = 'distance_star'
DISTANCE_END = 'distance_end'
UPDATE_END = 'update_end'
TRAVERSE_END = 'traverse_end'
SET_END = 'set_end'
# device
SEND_DOORBELL = 'send_doorbell'
RECV_DOORBELL = 'recv_doorbell'
RECV_SQ = 'recv_sq'
GET_QUERY_VECTOR_START = 'get_query_vector_start'
COMPUTATION_START = 'computation_start'
ALLOCATE_UNIT = 'allocate_unit'
DEALLOCATE_UNIT = 'deallocate_unit'
COMPUTATION_END = 'computation_end'
CQ_DMA_END = 'cq_dma_end'
POLLING_END = 'polling_end'


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