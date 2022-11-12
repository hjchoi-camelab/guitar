import os
import sys
import traceback
import pdb
from multiprocessing import Pool
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
NDP_NUM = int(sys.argv[4])
OPTION = int(sys.argv[5])

FILE = 'debug.log'
POSTFIX = "-JH-LATENCY"

ALL_COLUMNS = [
    "job",
    "timestamp",
    "latency",
]

HOST_DEV_ID = 100

INITIAL_VALUE = -1


### job ###
# device
DOORBELL = "doorbell"
SQ_DMA = "SQ DMA"
QUERY_VECTOR_DMA = "query vector DMA"
COMPUTATION = "computation"
CQ_DMA = "CQ DMA"
POLL = 'polling'

# host
UPDATE = "update"
GRAPH = "graph"
DISTANCE = "distance"
QUERY_VECTOR = "query vector"


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


def parsing(file_full_name):
    path = file_full_name[0]
    file = file_full_name[1]

    timestamps = []
    if OPTION == 0:
        output = path.split('/')[-1] + '-DEVICE' + POSTFIX
    elif OPTION == 1:
        output = path.split('/')[-1] + '-HOST' + POSTFIX
    elif OPTION == 2:
        output = path.split('/')[-1] + '-POLL' + POSTFIX
    else:
        print("broken")
        exit(1)
    for i in range(THREAD_NUM):
        timestamps.append([])
        for j in range(QUERY_DEPTH):
            timestamps[i].append({})
            for k in range(NDP_NUM):
                timestamps[i][j][k] = {
                    SEND_DOORBELL: 0,
                    RECV_DOORBELL: 0,
                    RECV_SQ: 0,
                    GET_QUERY_VECTOR_START: 0,
                    COMPUTATION_START: 0,
                    COMPUTATION_END: 0,
                    CQ_DMA_END: 0,
                    POLLING_END: 0,
                }
            timestamps[i][j][HOST_DEV_ID] = {
                SET_START: 0,
                QUERY_SET: 0,
                DISTANCE_START: 0,
                DISTANCE_END: 0,
                UPDATE_END: 0,
                TRAVERSE_END: 0,
                SET_END: 0,
            }
    print(f'{path}/{file}')
    f = open(f'{path}/{file}')
    lines = f.read().splitlines()
    out_list = []
    cq_dma_counter = 0
    cq_dma_timestamp = 0
    poll_counter = 0
    poll_timestamp = 0

    for line in lines:
        row = line.split(': ')
        timestamp = int(row[0])
        point = int(row[-1])
        dev_index = int(row[-2])
        query_index = int(row[-3])
        thread_id = int(row[-4])

        if OPTION == 0:
            if dev_index != HOST_DEV_ID:
                continue
            timestamps[thread_id][query_index][dev_index][point] = timestamp

            if point == QUERY_SET:
                latency = timestamp - timestamps[thread_id][query_index][dev_index][SET_START]
                out_list.append(dict(zip(ALL_COLUMNS, [QUERY_VECTOR, timestamp, latency])))
            elif point == DISTANCE_START:
                prev_timestamp = max(timestamps[thread_id][query_index][dev_index][QUERY_SET],
                                    timestamps[thread_id][query_index][dev_index][UPDATE_END])
                latency = timestamp - prev_timestamp
                out_list.append(dict(zip(ALL_COLUMNS, [GRAPH, timestamp, latency])))
            elif point == TRAVERSE_END:
                latency = timestamp - timestamps[thread_id][query_index][dev_index][UPDATE_END]
                out_list.append(dict(zip(ALL_COLUMNS, [GRAPH, timestamp, latency])))
            elif point == DISTANCE_END:
                latency = timestamp - timestamps[thread_id][query_index][dev_index][DISTANCE_START]
                out_list.append(dict(zip(ALL_COLUMNS, [DISTANCE, timestamp, latency])))
            elif point == UPDATE_END:
                prev_timestamp = max(timestamps[thread_id][query_index][dev_index][DISTANCE_END],
                                    timestamps[thread_id][query_index][dev_index][TRAVERSE_END])
                latency = timestamp - prev_timestamp
                out_list.append(dict(zip(ALL_COLUMNS, [UPDATE, timestamp, latency])))
            elif point == SET_END:
                prev_timestamp = max(timestamps[thread_id][query_index][dev_index][DISTANCE_END],
                                    timestamps[thread_id][query_index][dev_index][TRAVERSE_END])
                latency = timestamp - prev_timestamp
                out_list.append(dict(zip(ALL_COLUMNS, [UPDATE, timestamp, latency])))
        elif OPTION == 1:
            if dev_index == HOST_DEV_ID:
                continue
            timestamps[thread_id][query_index][dev_index][point] = timestamp

            if point == RECV_DOORBELL:
                latency = timestamp - timestamps[thread_id][query_index][dev_index][SEND_DOORBELL]
                out_list.append(dict(zip(ALL_COLUMNS, [DOORBELL, timestamp, latency])))
            elif point == RECV_SQ:
                latency = timestamp - timestamps[thread_id][query_index][dev_index][RECV_DOORBELL]
                out_list.append(dict(zip(ALL_COLUMNS, [SQ_DMA, timestamp, latency])))
            elif point == COMPUTATION_START:
                if timestamps[thread_id][query_index][dev_index][RECV_SQ] < \
                timestamps[thread_id][query_index][dev_index][GET_QUERY_VECTOR_START]:
                    latency = timestamp - timestamps[thread_id][query_index][dev_index][GET_QUERY_VECTOR_START]
                    out_list.append(dict(zip(ALL_COLUMNS, [QUERY_VECTOR_DMA, timestamp, latency])))
            elif point == COMPUTATION_END:
                latency = timestamp - timestamps[thread_id][query_index][dev_index][COMPUTATION_START]
                out_list.append(dict(zip(ALL_COLUMNS, [COMPUTATION, timestamp, latency])))
            elif point == CQ_DMA_END:
                latency = timestamp - timestamps[thread_id][query_index][dev_index][COMPUTATION_END]
                out_list.append(dict(zip(ALL_COLUMNS, [CQ_DMA, timestamp, latency])))
            elif point == POLLING_END:
                latency = timestamp - timestamps[thread_id][query_index][dev_index][CQ_DMA_END]
                out_list.append(dict(zip(ALL_COLUMNS, [POLL, timestamp, latency])))
        elif OPTION == 2:
            if point == CQ_DMA_END:
                # update counter
                if cq_dma_counter == NDP_NUM:
                    cq_dma_counter = 0
                cq_dma_counter += 1

                # log if last
                if cq_dma_counter == NDP_NUM:
                    if timestamps[thread_id][query_index][dev_index][COMPUTATION_END] < timestamps[thread_id][query_index][HOST_DEV_ID][POLLING_END]:
                        latency = timestamps[thread_id][query_index][HOST_DEV_ID][POLLING_END] - timestamps[thread_id][query_index][dev_index][COMPUTATION_END]
                    else:
                        latency = timestamp - timestamps[thread_id][query_index][dev_index][COMPUTATION_END]
                    out_list.append(dict(zip(ALL_COLUMNS, [CQ_DMA, timestamp, latency])))
                    cq_dma_timestamp = timestamp
            elif point == POLLING_END:
                # update counter
                if poll_counter == NDP_NUM:
                    poll_counter = 0
                poll_counter += 1

                # log if last
                if poll_counter == NDP_NUM:
                    if cq_dma_counter == NDP_NUM:
                        latency = timestamp - cq_dma_timestamp
                    else:
                        latency = 0
                    out_list.append(dict(zip(ALL_COLUMNS, [POLL, timestamp, latency])))

            timestamps[thread_id][query_index][dev_index][point] = timestamp

    df = pd.DataFrame(out_list, columns=ALL_COLUMNS)
    df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
    print(output)
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