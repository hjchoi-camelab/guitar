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

if THREAD_NUM != 1:
    print("This script is for single-core")
    exit(1)

FILE = 'debug.log'
POSTFIX = "-DEVICE-UTILIZATION"
HOST_DEV_ID = 100
INITIAL_VALUE = -1
HOST = 0
DEVICE = 1
BOTH = 2

COLUMNS = ["timestamp"]
for i in range(NDP_NUM):
    COLUMNS.append(f"{i}")

def get_init_list():
    _tmp_list = []
    columns = COLUMNS

    for column in columns:
        _tmp_list.append(0)

    return _tmp_list


def get_header():
    return COLUMNS


def set_state(stateManager, timestamp, dev_index, point):
    stateManager.set_point(timestamp, dev_index, point)


class StateManager():
    def __init__(self, query_depth, ndp_num, units_per_device, csv_writer):
        self.query_depth = query_depth
        self.ndp_num = ndp_num
        self.units_per_device = units_per_device
        self.utilizations = []
        self.allocated_unit_nums = []
        self.csv_writer = csv_writer
        self.states = get_init_list()

        for i in range(ndp_num):
            self.utilizations.append(0)
            self.allocated_unit_nums.append(0)
        self.csv_writer.writerow(get_header())


    def update_utilization(self, dev_index, allocated):
        if allocated:
            value = 1
        else:
            value = -1
        self.allocated_unit_nums[dev_index] += value
        self.utilizations[dev_index] = self.allocated_unit_nums[dev_index] / self.units_per_device


    def get_utilization(self, dev_index):
        return self.utilizations[dev_index]


    def set_point(self, timestamp, dev_index, point):
        self.update_utilization(dev_index, point == ALLOCATE_UNIT)
        self.states[0] = timestamp
        self.states[dev_index + 1] = self.get_utilization(dev_index)
        self.csv_writer.writerow(self.states)



### point ###
# host
SET_START = 'set_start'
QUERY_SET = 'query_set'
DISTANCE_START = 'distance_start'
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
POINTS = {
    SET_START: None,
    QUERY_SET: None,
    DISTANCE_START: None,
    DISTANCE_END: None,
    UPDATE_END: None,
    TRAVERSE_END: None,
    SET_END: None,
    SEND_DOORBELL: None,
    RECV_DOORBELL: None,
    RECV_SQ: None,
    GET_QUERY_VECTOR_START: None,
    COMPUTATION_START: None,
    ALLOCATE_UNIT: set_state,
    DEALLOCATE_UNIT: set_state,
    COMPUTATION_END: None,
    CQ_DMA_END: None,
    POLLING_END: None,
}


# global list
row_list = []
out_row_list = []

def parsing(file_full_name):
    path = file_full_name[0]
    file = file_full_name[1]
    output = path.split('/')[-1] + POSTFIX

    print(f'{path}/{file}')
    f = open(f'{path}/{file}')
    # csv_f = open(f'{DIRECTORY}/{output}.csv', 'w', newline='')
    csv_f = open(f'{DIRECTORY}/{output}.csv', 'w', newline='')
    wr = csv.writer(csv_f)
    state_manager = StateManager(QUERY_DEPTH, NDP_NUM, UNIT_NUM, wr)

    lines = f.read().splitlines()
    for line in lines:
        row = line.split(': ')
        timestamp = int(row[0])
        point = row[-1]
        dev_index = int(row[-2])

        if not POINTS[point]:
            continue

        POINTS[point](state_manager, timestamp, dev_index, point)

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
    with Pool(18) as p:
        p.map(parsing, file_full_names)