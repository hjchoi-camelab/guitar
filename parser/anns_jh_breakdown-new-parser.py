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

# usage "python anss_jh_breakdown-parser.py [log directory] [# of the thread] [query depth] [# of the NDP device]"

OUTLIER_THRESHOLD = 50000000

DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]
THREAD_NUM = int(sys.argv[2])
QUERY_DEPTH = int(sys.argv[3])
NDP_NUM = int(sys.argv[4])
QUERY_NUM = int(sys.argv[5])
if len(sys.argv) == 7:
    TYPE = sys.argv[6]
else:
    TYPE = ""

FILE = 'debug.log'
TERMINAL_FILE = 'system.terminal'
POSTFIX = "-BREAKDOWN"

TYPE_LIST = [
    'disk',
    'distributed',
    'base',
    'ndp',
    'cache',
    'nearest',
    'infinite',
]

NDP_LIST = [
    'ndp',
    'cache',
    'nearest',
    'infinite',
]

COLUMNS = [
    "update",
    "calculation",
    "graph",
    "query vector",
    "sq entry set",
    "doorbell",
    "sq dma",
    "cq dma",
    "polling",
    "accumulation",
    "distributed_update",
    "network_memcpy",
    "network_link",
    "total",
]

RDMA_PATTERN = r'([\d \+]* \d*)(?= B)'
RDMA_REGEX = re.compile(RDMA_PATTERN)

ACCURACY_PATTERN = r'([0-9]*[.]?[0-9]+) ([+-]?([0-9]*[.])?[0-9]+) [+-]?([0-9]*[.])?[0-9]+ [+-]?([0-9]*[.])?[0-9]+'
ACCURACY_REGEX = re.compile(ACCURACY_PATTERN)

DATASET_PATTERN = r'(?<=datasetDir: ")[\s\S]*\/(\w*)(?=")'
DATASET_REGEX = re.compile(DATASET_PATTERN)

def getInitDict():
    _tmp_dict = {}
    for column in COLUMNS:
        _tmp_dict[column] = 0
    return _tmp_dict

OUT_COLUMNS = ["dataset", "search-L", "type"]
OUT_COLUMNS.extend(COLUMNS)
OUT_COLUMNS.extend(["end-to-end", "accuracy", "num query", "num ndp"])

MAGIC_WORDS = ['P', 'Q', 'm5_print']

INITIAL_VALUE = -1

### point ###
# host
SET_START = 'set_start'
QUERY_SET = 'query_set'
DISTANCE_START = 'distance_start'
SEND_DOORBELL_DONE = 'send_doorbell_done'
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
# distributed
DISTRIBUTED_MASTER_SEND = 'distributed_master_send'
DISTRIBUTED_SLAVE_RECV = 'distributed_slave_recv'
DISTRIBUTED_SLAVE_SEND = 'distributed_slave_send'
DISTRIBUTED_MASTER_RECV = 'distributed_master_recv'
DISTRIBUTED_POSTPROCESSING = 'distributed_postprocessing'
DISTRIBUTED_MERGE_END = 'distributed_merge_end'

DISTRIBUTED_POINT_LIST = [
    DISTRIBUTED_MASTER_SEND,
    DISTRIBUTED_SLAVE_RECV,
    DISTRIBUTED_SLAVE_SEND,
    DISTRIBUTED_MASTER_RECV,
    DISTRIBUTED_POSTPROCESSING,
    DISTRIBUTED_MERGE_END,
]


# global list
out_row_list = []


class OneQuery:
    def __init__(self, type, thread_id, query_index, ndp_num=0, interface="dmaone"):
        self.type = type
        self.thread_id = thread_id
        self.query_index = query_index
        self.ndp_num = ndp_num
        self.interface = interface

        self.doorbell_counter = 0
        self.first_doorbell = 0
        self.cq_dma_counter = 0
        self.polling_counter = 0
        self.timestamps = {
            SET_START: 0,
            QUERY_SET: 0,
            DISTANCE_START: 0,
            SEND_DOORBELL: 0,
            RECV_DOORBELL: 0,
            RECV_SQ: 0,
            GET_QUERY_VECTOR_START: 0,
            COMPUTATION_START: 0,
            COMPUTATION_END: 0,
            CQ_DMA_END: 0,
            POLLING_END: 0,
            DISTANCE_END: 0,
            UPDATE_END: 0,
            TRAVERSE_END: 0,
            SET_END: 0,
        }
        self.ticks = getInitDict()

    def one_hop_reset(self):
        self.doorbell_counter = 0
        self.first_doorbell = 0
        self.cq_dma_counter = 0
        self.polling_counter = 0
        self.timestamps = {
            SET_START: 0,
            QUERY_SET: 0,
            DISTANCE_START: 0,
            SEND_DOORBELL: 0,
            RECV_DOORBELL: 0,
            RECV_SQ: 0,
            GET_QUERY_VECTOR_START: 0,
            COMPUTATION_START: 0,
            COMPUTATION_END: 0,
            CQ_DMA_END: 0,
            POLLING_END: 0,
            DISTANCE_END: 0,
            UPDATE_END: 0,
            TRAVERSE_END: 0,
            SET_END: 0,
        }

    def query_reset(self):
        self.one_hop_reset()
        self.ticks = getInitDict()

    def update_ticks(self, timestamp):
        if self.type in NDP_LIST:
            if self.timestamps[SET_START] != 0:
                assert self.timestamps[QUERY_SET] != 0
                if self.interface == 'dmaone' or self.interface == 'dma':
                    assert self.timestamps[GET_QUERY_VECTOR_START] != 0
                    self.ticks["query vector"] += self.timestamps[COMPUTATION_START] - self.timestamps[GET_QUERY_VECTOR_START]
                self.ticks["query vector"] += self.timestamps[QUERY_SET] - self.timestamps[SET_START]

                self.ticks["graph"] += self.timestamps[DISTANCE_START] - self.timestamps[QUERY_SET]
                self.ticks["update"] += timestamp - self.timestamps[DISTANCE_END]
            elif self.timestamps[TRAVERSE_END] == 0:
                self.ticks["graph"] += self.timestamps[DISTANCE_START] - self.timestamps[UPDATE_END]
                self.ticks["update"] += timestamp - self.timestamps[DISTANCE_END]
            else:
                self.ticks["graph"] += self.timestamps[TRAVERSE_END] - self.timestamps[UPDATE_END]
                self.ticks["update"] += timestamp - self.timestamps[TRAVERSE_END]

            if self.interface == 'dmaone':
                if  self.timestamps[DISTANCE_START] < self.first_doorbell:
                    self.ticks["sq entry set"] += self.first_doorbell - self.timestamps[DISTANCE_START]
                    self.ticks["doorbell"] += self.timestamps[RECV_DOORBELL] - self.first_doorbell
            else:
                self.ticks["sq entry set"] += self.timestamps[SEND_DOORBELL] - self.timestamps[DISTANCE_START]
                self.ticks["doorbell"] += self.timestamps[RECV_DOORBELL] - self.timestamps[SEND_DOORBELL]

            if self.interface != 'mmio':
                self.ticks["sq dma"] += self.timestamps[RECV_SQ] - self.timestamps[RECV_DOORBELL]

            self.ticks["calculation"] += self.timestamps[COMPUTATION_END] - self.timestamps[COMPUTATION_START]

            if self.cq_dma_counter != self.ndp_num:
                self.ticks["cq dma"] += self.timestamps[POLLING_END] - self.timestamps[COMPUTATION_END]
            else:
                self.ticks["cq dma"] += min(self.timestamps[CQ_DMA_END], self.timestamps[POLLING_END]) - self.timestamps[COMPUTATION_END]
                if (self.timestamps[POLLING_END] - min(self.timestamps[CQ_DMA_END], self.timestamps[POLLING_END]) < OUTLIER_THRESHOLD):
                    self.ticks["polling"] += self.timestamps[POLLING_END] - min(self.timestamps[CQ_DMA_END], self.timestamps[POLLING_END])
                # if self.timestamps[POLLING_END] - min(self.timestamps[CQ_DMA_END], self.timestamps[POLLING_END]):
                #     print(f'{timestamp}: {self.timestamps[POLLING_END]}, {self.timestamps[CQ_DMA_END]}, {self.timestamps[POLLING_END] - self.timestamps[CQ_DMA_END]}')

            if  self.timestamps[DISTANCE_START] < self.first_doorbell:
                self.ticks["accumulation"] += self.timestamps[DISTANCE_END] - self.timestamps[POLLING_END]
        else:
            if self.timestamps[SET_START] != 0:
                self.ticks["graph"] += self.timestamps[DISTANCE_START] - self.timestamps[SET_START]
            else:
                self.ticks["graph"] += self.timestamps[DISTANCE_START] - self.timestamps[UPDATE_END]
            self.ticks["calculation"] += self.timestamps[DISTANCE_END] - self.timestamps[DISTANCE_START]
            self.ticks["update"] += timestamp - self.timestamps[DISTANCE_END]

        self.one_hop_reset()


    def error(self, log_line):
        print(log_line)
        traceback.print_tb()
        exit(1)

    def insert_timestamp(self, point, timestamp, log_line, row_list):
        if point == UPDATE_END or point == SET_END:
            self.update_ticks(timestamp)

        # increment doorbell counter
        if point == SEND_DOORBELL:
            if self.doorbell_counter == 0:
                self.first_doorbell = timestamp
            self.doorbell_counter += 1

        # increment CQ DMA counter
        if point == CQ_DMA_END and \
           self.timestamps[COMPUTATION_END] != 0 :
            self.cq_dma_counter += 1

        if point == POLLING_END:
            self.polling_counter += 1
        if point == TRAVERSE_END:
            self.polling_counter += self.ndp_num

        # insert timestamp
        self.timestamps[point] = timestamp

        if point == SET_END:
            self.ticks['total'] = sum(self.ticks.values())
            row_list.append(self.ticks)
            self.query_reset()


def update_distributed_tick(timestamp, point, distributed, network_memcpy, network_update):
    if point == DISTRIBUTED_POSTPROCESSING:
        network_memcpy += distributed[DISTRIBUTED_SLAVE_RECV] - distributed[DISTRIBUTED_MASTER_SEND]
        network_memcpy += distributed[DISTRIBUTED_MASTER_RECV] - distributed[DISTRIBUTED_SLAVE_SEND]
        network_update += timestamp - distributed[DISTRIBUTED_MASTER_RECV]
    elif point == DISTRIBUTED_MERGE_END:
        network_update += timestamp - distributed[DISTRIBUTED_POSTPROCESSING]
    else:
        print("Wrong point")
        exit(1)

    return (network_memcpy, network_update)


def parsing(file_full_name):
    path = file_full_name[0]
    file = file_full_name[1]

    setting = path.split('/')[-1]
    if TYPE:
        type = TYPE
    else:
        type = setting.split('_')[-1]
    if type not in TYPE_LIST:
        print(f"wrong type: {type}")
        exit(1)
    elif type == 'nearest':
        query_depth = QUERY_DEPTH
    else:
        query_depth = 1

    if type in NDP_LIST:
        ndp_num = NDP_NUM
    elif type == "distributed":
        ndp_num = NDP_NUM + 1
    else:
        ndp_num = 0

    # get end-to-end latency
    start_tick = 0
    end_to_end = 0
    is_first = True

    dataset = ''
    accuracy = 0
    search_l = 0

    queries = []
    for i in range(THREAD_NUM):
        queries.append([])
        for j in range(query_depth):
            queries[i].append(OneQuery(type, i, j, ndp_num))

    # distributed
    distributed = {
        DISTRIBUTED_MASTER_SEND: 0,
        DISTRIBUTED_SLAVE_RECV: 0,
        DISTRIBUTED_SLAVE_SEND: 0,
        DISTRIBUTED_MASTER_RECV: 0,
        DISTRIBUTED_POSTPROCESSING: 0,
        DISTRIBUTED_MERGE_END: 0,
    }
    distributed_update = 0
    network_memcpy = 0
    network_link = 0

    row_list = []
    output = setting + POSTFIX

    print(f'{path}/{file}')
    f = open(f'{path}/{file}')
    lines = f.read().splitlines()
    for line in lines:
        row = line.split(': ')
        magic_word = row[2]
        if magic_word not in MAGIC_WORDS:
            continue

        # distributed
        if magic_word == 'm5_print':
            rdma_matching = RDMA_REGEX.search(line)
            # 3.7 us per 512 bytes
            network_link += (eval(rdma_matching.group()) / 512 * 3700000)
            continue

        tick = int(row[0])
        point = row[-1]
        # dev_index = int(row[-2])
        query_index = int(row[-3])
        thread_id = int(row[-4])

        # print(line)

        # distributed
        if point in DISTRIBUTED_POINT_LIST:
            if point == DISTRIBUTED_POSTPROCESSING or point == DISTRIBUTED_MERGE_END:
                (network_memcpy, distributed_update) = update_distributed_tick(tick, point, distributed, network_memcpy, distributed_update)
            distributed[point] = tick
            continue

        queries[thread_id][query_index].insert_timestamp(point, tick, line, row_list)

        if point == SET_START and is_first:
            start_tick = tick
            is_first = False
    end_to_end = tick - start_tick


    # get accuracy
    # get search-l
    terminal_file = open(os.path.join(path, TERMINAL_FILE))
    lines = terminal_file.read().splitlines()
    for line in lines:
        dataset_match = DATASET_REGEX.search(line)
        if dataset_match:
            dataset = dataset_match.group(1)
        accuracy_match = ACCURACY_REGEX.search(line)
        if accuracy_match:
            accuracy = float(accuracy_match.group(2))
            search_l = int(accuracy_match.group(1))

    df = pd.DataFrame(row_list, columns=COLUMNS).fillna(0).astype(int)

    # distributed
    if type == 'distributed':
        end_to_end += distributed_update + network_memcpy + network_link
        end_to_end //= 5
        distributed_update //= (ndp_num * QUERY_NUM)
        network_memcpy //= (ndp_num * QUERY_NUM)
        network_link //= (ndp_num * QUERY_NUM)
        df['total'] += distributed_update + network_memcpy + network_link
        df['distributed_update'] = distributed_update
        df['network_memcpy'] = network_memcpy
        df['network_link'] = network_link

    # generate mean
    mean = df.mean().values.tolist()
    mean = [dataset, search_l, type] + mean
    mean.extend([end_to_end, accuracy, QUERY_NUM, ndp_num])

    df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
    f.close()

    return mean


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
        means = p.map(parsing, file_full_names)

    output = DIRECTORY.split('/')[-1] + POSTFIX
    df = pd.DataFrame(means, columns=OUT_COLUMNS).fillna(0)
    df['search-L'] = pd.to_numeric(df['search-L'])
    df.sort_values(["type", "search-L"],
        axis=0,
        ascending=[True, True],
        inplace=True)
    print(df)

    df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
    # df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
