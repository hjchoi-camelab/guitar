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

MAGIC_CHARACTERS = ['P', 'Q']

INITIAL_VALUE = -1

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


# global list
row_list = []
out_row_list = []


class OneQuery:
    def __init__(self, thread_id, query_index, ndp_num, interface):
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
        assert self.polling_counter == 4

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

        if self.interface == 'dmaone':
            self.ticks["sq entry set"] += self.first_doorbell - self.timestamps[DISTANCE_START]
            self.ticks["doorbell"] += self.timestamps[RECV_DOORBELL] - self.first_doorbell
        else:
            self.ticks["sq entry set"] += self.timestamps[SEND_DOORBELL] - self.timestamps[DISTANCE_START]
            self.ticks["doorbell"] += self.timestamps[RECV_DOORBELL] - self.timestamps[SEND_DOORBELL]

        if self.interface != 'mmio':
            self.ticks["sq dma"] += self.timestamps[RECV_SQ] - self.timestamps[RECV_DOORBELL]

        self.ticks["calculation"] += self.timestamps[COMPUTATION_END] - self.timestamps[COMPUTATION_START]

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
        if point == UPDATE_END or point == SET_END:
            self.update_ticks(timestamp)

        # increment doorbell counter
        if point == SEND_DOORBELL:
            if self.doorbell_counter == 0:
                self.first_doorbell = timestamp
            self.doorbell_counter += 1

        # increment CQ DMA counter
        if point == CQ_DMA_END and                                      \
           self.timestamps[COMPUTATION_END] != 0 :
            self.cq_dma_counter += 1

        if point == POLLING_END:
            self.polling_counter += 1

        # insert timestamp
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
            if row[-5] not in MAGIC_CHARACTERS:
                continue
            tick = int(row[0])
            point = row[-1]
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
df.sort_values(["type"],
    axis=0,
    ascending=[True],
    inplace=True)
print(df)

df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
# df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
