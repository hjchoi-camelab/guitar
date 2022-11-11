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

# usage "python anns_jh_latency.py [log directory] [# of the thread] [query depth] [# of the NDP device]"

DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]
THREAD_NUM = int(sys.argv[2])
QUERY_DEPTH = int(sys.argv[3])

FILE = 'debug.log'
STAT_FILE = 'stats.txt'
POSTFIX = "-GRAPH-LATENCY"

HOST_DEV_ID = 100

INITIAL_VALUE = -1

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

ONES_COLUMNS = [
    "type",
    "timestamp",
    "latency",
]

def getGraphLatency(path):
    graph_list = []
    timestamps = []

    for i in range(THREAD_NUM):
        timestamps.append([])
        for j in range(QUERY_DEPTH):
            timestamps[i].append({})
            timestamps[i][j][HOST_DEV_ID] = {
                SET_START: 0,
                QUERY_SET: 0,
                EP_SET: 0,
                RANDOM_START: 0,
                DISTANCE_START: 0,
                POLLING_END: 0,
                DISTANCE_END: 0,
                UPDATE_END: 0,
                TRAVERSE_END: 0,
                SET_END: 0,
            }
    f = open(f'{path}/{file}')
    lines = f.read().splitlines()


    for line in lines:
        row = line.split(': ')
        timestamp = int(row[0])
        point = int(row[-1])
        dev_index = int(row[-2])
        query_index = int(row[-3])
        thread_id = int(row[-4])

        if dev_index != HOST_DEV_ID:
            continue

        timestamps[thread_id][query_index][dev_index][point] = timestamp

        if point == DISTANCE_START:
            prev_timestamp = max(timestamps[thread_id][query_index][dev_index][QUERY_SET],
                                timestamps[thread_id][query_index][dev_index][UPDATE_END])
            latency = timestamp - prev_timestamp
            graph_list.append(dict(zip(ONES_COLUMNS, ['graph_end', timestamp, latency])))
        elif point == TRAVERSE_END:
            latency = timestamp - timestamps[thread_id][query_index][dev_index][UPDATE_END]
            graph_list.append(dict(zip(ONES_COLUMNS, ['graph_end', timestamp, latency])))
        elif point == QUERY_SET:
            graph_list.append(dict(zip(ONES_COLUMNS, ['graph_start', timestamp, 1000000])))
        elif point == UPDATE_END:
            graph_list.append(dict(zip(ONES_COLUMNS, ['graph_start', timestamp, 1000000])))

    f.close()
    return graph_list


final_graph_list = []

for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file != FILE:
            continue
        print(f'{path}/{file}')
        output = path.split('/')[-1] + POSTFIX

        # get graph latency
        graph_list = getGraphLatency(path)
        final_graph_list.extend(graph_list)

        df = pd.DataFrame(graph_list, columns=ONES_COLUMNS)
        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)

# graph_df = pd.DataFrame(final_graph_list, columns=ONES_COLUMNS)
# graph_df.to_csv(f'{DIRECTORY}/graph-latency.csv', index=False)
