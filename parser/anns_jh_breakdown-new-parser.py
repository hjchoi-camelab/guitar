import os
import sys
import traceback
import pdb
import numpy as np
import pandas as pd
from math import log
from collections import Counter
from functools import reduce
from operator import add

# usage "python anss_jh_breakdown-parser.py [log directory] [# of the thread] [query depth] [# of the NDP device]"

DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]
THREAD_NUM = int(sys.argv[2])
QUERY_DEPTH = int(sys.argv[3])
NDP_NUM = int(sys.argv[4])

FILE = 'debug.log'
POSTFIX = "-JH-BREAKDOWN"

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
    "total",
]

def getInitDict():
    _tmp_dict = {}
    for column in COLUMNS:
        _tmp_dict[column] = 0
    return _tmp_dict

OUT_COLUMNS = ["type"]
OUT_COLUMNS.extend(COLUMNS)

INITIAL_VALUE = -1

# point
SET_START = 0
QUERY_SET = (SET_START + 1)
DISTANCE_START = (QUERY_SET + 1)
DISTANCE_END = (DISTANCE_START + 1)
UPDATE_END = (DISTANCE_END + 1)
TRAVERSE_END = (UPDATE_END + 1)
SET_END = (TRAVERSE_END + 1)

SEND_DOORBELL = 1000
RECV_DOORBELL = (SEND_DOORBELL + 1)
RECV_SQ = (RECV_DOORBELL + 1)
GET_QUERY_VECTOR_START = (RECV_SQ + 1)
COMPUTATION_START = (GET_QUERY_VECTOR_START + 1)
ALLOCATE_UNIT = (COMPUTATION_START + 1)
DEALLOCATE_UNIT = (ALLOCATE_UNIT + 1)
COMPUTATION_END = (DEALLOCATE_UNIT + 1)
CQ_DMA_END = (COMPUTATION_END + 1)
POLLING_END = (CQ_DMA_END + 1)


# global list
row_list = []
out_row_list = []


class OneQuery:
    def __init__(self, thread_id, query_index, ndp_num, interface):
        self.thread_id = thread_id
        self.query_index = query_index
        self.ndp_num = ndp_num
        self.interface = interface

        self.cq_dma_counter = 0
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
        self.cq_dma_counter = 0
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
        if self.timestamps[SET_START] != 0:
            if self.interface == 'mmio':
                assert self.timestamps[QUERY_SET] != 0
            elif self.interface == 'dmaone' or self.interface == 'dma':
                assert self.timestamps[QUERY_SET] != 0 and              \
                    self.timestamps[GET_QUERY_VECTOR_START] != 0
                self.ticks["query vector"] += self.timestamps[COMPUTATION_START] - self.timestamps[GET_QUERY_VECTOR_START]
            else:
                print("unknown interface")
                exit(1)
            self.ticks["query vector"] += self.timestamps[QUERY_SET] - self.timestamps[SET_START]
            self.ticks["graph"] += self.timestamps[DISTANCE_START] - self.timestamps[QUERY_SET]
        else:
            self.ticks["graph"] += self.timestamps[DISTANCE_START] - self.timestamps[UPDATE_END]

        self.ticks["sq entry set"] += self.timestamps[SEND_DOORBELL] - self.timestamps[DISTANCE_START]
        self.ticks["doorbell"] += self.timestamps[RECV_DOORBELL] - self.timestamps[SEND_DOORBELL]
        if self.interface != 'mmio':
            self.ticks["sq dma"] += self.timestamps[RECV_SQ] - self.timestamps[RECV_DOORBELL]
        self.ticks["calculation"] += self.timestamps[COMPUTATION_END] - self.timestamps[COMPUTATION_START]
        # if self.timestamps[CQ_DMA_END] < self.timestamps[COMPUTATION_END]:
        if self.cq_dma_counter != NDP_NUM:
            self.ticks["cq dma"] += self.timestamps[POLLING_END] - self.timestamps[COMPUTATION_END]
        # else:
        else:
            self.ticks["cq dma"] += min(self.timestamps[CQ_DMA_END], self.timestamps[POLLING_END]) - self.timestamps[COMPUTATION_END]
            self.ticks["polling"] += self.timestamps[POLLING_END] - min(self.timestamps[CQ_DMA_END], self.timestamps[POLLING_END])
        self.ticks["accumulation"] += self.timestamps[DISTANCE_END] - self.timestamps[POLLING_END]
        self.ticks["update"] += timestamp - self.timestamps[DISTANCE_END]

        self.one_hop_reset()

    def error(self, log_line):
        print(log_line)
        traceback.print_tb()
        exit(1)

    def insert_timestamp(self, point, timestamp, log_line):
        if point < SET_START or SET_END < point:
            self.error(log_line)

        if point == UPDATE_END or point == SET_END:
            self.update_ticks(timestamp)

        if point == CQ_DMA_END and                                      \
           self.timestamps[COMPUTATION_END] < timestamp:
            self.cq_dma_counter += 1
        self.timestamps[point] = timestamp

        if point == SET_END:
            self.ticks['total'] = sum(self.ticks.values())
            row_list.append(self.ticks)
            self.query_reset()


for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file != FILE:
            continue
        interface = path.split('/')[-1].split('-')[-1]
        prev_tick = 0
        prev_point = 0
        queries = []
        for i in range(THREAD_NUM):
            queries.append([])
            for j in range(QUERY_DEPTH):
                queries[i].append(OneQuery(i, j, NDP_NUM, interface))
        row_list = []
        output = path.split('/')[-1] + POSTFIX

        print(f'{path}/{file}')
        f = open(f'{path}/{file}')
        lines = f.read().splitlines()
        for line in lines:
            row = line.split(': ')
            tick = int(row[0])
            point = int(row[-1])
            # dev_index = int(row[-2])
            query_index = int(row[-3])
            thread_id = int(row[-4])
            queries[thread_id][query_index].insert_timestamp(point, tick, line)

        df = pd.DataFrame(row_list, columns=COLUMNS).fillna(0).astype(int)
        mean = df.mean().values.tolist()
        mean = [output] + mean
        out_row_list.append(mean)

        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
        # df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
        f.close()

output = DIRECTORY.split('/')[-1] + POSTFIX
df = pd.DataFrame(out_row_list, columns=OUT_COLUMNS)
df.sort_values(["graph"],
    axis=0,
    ascending=[True],
    inplace=True)
print(df)

df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
# df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
