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
    "distance",
    "graph",
    "query vector",
    "submission",
    "cq dma",
    "polling",
    "accumulation",
    "total",
]

OUT_COLUMNS = ["type"]
OUT_COLUMNS.extend(COLUMNS)

INITIAL_VALUE = -1

# point
SET_START = 0
QUERY_SET = (SET_START + 1)
DISTANCE_START = (QUERY_SET + 1)
GET_QUERY_VECTOR_START = (DISTANCE_START + 1)
COMPUTATION_START = (GET_QUERY_VECTOR_START + 1)
COMPUTATION_END = (COMPUTATION_START + 1)
CQ_DMA_END = (COMPUTATION_END + 1)
POLLING_END = (CQ_DMA_END + 1)
DISTANCE_END = (POLLING_END + 1)
UPDATE_END = (DISTANCE_END + 1)
TRAVERSE_END = (UPDATE_END + 1)
SET_END = (TRAVERSE_END + 1)

# state
INIT = 0
SUBMISSION = INIT + 1
QUERY = SUBMISSION + 1
COMPUTATION = QUERY + 1
CQ_DMA = COMPUTATION + 1
POLLING = CQ_DMA + 1
HOST = POLLING + 1

# global list
row_list = []
out_row_list = []


class OneQuery:
    def __init__(self, thread_id, query_index, ndp_num):
        self.thread_id = thread_id
        self.query_index = query_index
        self.ndp_num = ndp_num

        self.state = INIT
        self.submission_counter = 0
        self.query_counter = 0
        self.computation_counter = 0
        self.cq_dma_counter = 0
        self.prev_point = INITIAL_VALUE
        self.prev_tick = INITIAL_VALUE
        self.ticks = {
            "update": 0,
            "distance": 0,
            "graph": 0,
            "query vector": 0,
            "submission": 0,
            "cq dma": 0,
            "polling": 0,
            "accumulation": 0,
            "total": 0,
        }

    def reset(self):
        self.state = INIT
        self.submission_counter = 0
        self.query_counter = 0
        self.computation_counter = 0
        self.cq_dma_counter = 0
        self.prev_tick = INITIAL_VALUE
        self.prev_point = INITIAL_VALUE
        self.ticks = {
            "update": 0,
            "distance": 0,
            "graph": 0,
            "query vector": 0,
            "submission": 0,
            "cq dma": 0,
            "polling": 0,
            "accumulation": 0,
            "total": 0,
        }

    def error(self, log_line):
        print(log_line)
        traceback.print_tb()
        exit(1)

    def increase_submission_counter(self):
        self.submission_counter += 1
        if self.submission_counter == NDP_NUM:
            self.state = COMPUTATION

    def increase_query_counter(self):
        self.query_counter += 1
        if self.query_counter == NDP_NUM:
            self.state = QUERY

    def increase_computation_counter(self):
        self.computation_counter += 1
        if self.computation_counter == NDP_NUM:
            self.state = CQ_DMA

    def increase_cq_dma_counter(self):
        self.cq_dma_counter += 1
        if self.cq_dma_counter == NDP_NUM:
            self.state = POLLING

    def reset_counter(self):
        self.submission_counter = 0
        self.query_counter = 0
        self.computation_counter = 0
        self.cq_dma_counter = 0

    def insert_tick(self, point, tick, log_line):
        time_interval = tick - self.prev_tick

        if point == SET_START:
            pass
        elif self.prev_point == SET_START:
            assert point == QUERY_SET or                        \
                   point == DISTANCE_START or                   \
                   point == CQ_DMA_END
            if point == QUERY_SET:
                self.ticks["query vector"] += time_interval
            elif point == DISTANCE_START:
                self.ticks["graph"] += time_interval
            elif point == CQ_DMA_END:
                self.tmp_tick = time_interval
            else:
                self.error(log_line)
        elif self.prev_point == QUERY_SET:
            assert point == DISTANCE_START
            self.ticks["graph"] += time_interval
        elif self.prev_point == DISTANCE_START:
            assert point == COMPUTATION_START or                \
                   point == GET_QUERY_VECTOR_START or           \
                   point == DISTANCE_END
            if point == COMPUTATION_START:
                self.ticks["submission"] += time_interval
                self.state = SUBMISSION
                self.increase_submission_counter()
            elif point == GET_QUERY_VECTOR_START:
                self.state = SUBMISSION
                self.ticks["submission"] += time_interval
                self.increase_query_counter()
            elif point == DISTANCE_END:
                # NOT USING JH CASE
                self.ticks["distance"] += time_interval
            else:
                self.error(log_line)
        elif self.prev_point == GET_QUERY_VECTOR_START:
            assert point == GET_QUERY_VECTOR_START or           \
                   point == COMPUTATION_START or                \
                   point == COMPUTATION_END or                  \
                   point == CQ_DMA_END
            if point == GET_QUERY_VECTOR_START:
                self.ticks["submission"] += time_interval
                self.increase_query_counter()
            elif point == COMPUTATION_START:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                else:
                    self.error(log_line)
                self.increase_submission_counter()
            elif point == COMPUTATION_END:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                else:
                    self.error(log_line)
                self.increase_computation_counter()
            elif point == CQ_DMA_END:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                else:
                    self.error(log_line)
                self.increase_cq_dma_counter()
            else:
                self.error(log_line)
        elif self.prev_point == COMPUTATION_START:
            assert point == GET_QUERY_VECTOR_START or           \
                   point == COMPUTATION_START or                \
                   point == COMPUTATION_END or                  \
                   point == CQ_DMA_END
            if point == GET_QUERY_VECTOR_START:
                self.ticks["submission"] += time_interval
                self.increase_query_counter()
            elif point == COMPUTATION_START:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                else:
                    self.error(log_line)
                self.increase_submission_counter()
            elif point == COMPUTATION_END:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                elif self.state == COMPUTATION:
                    self.ticks["distance"] += time_interval
                else:
                    self.error(log_line)
                self.increase_computation_counter()
            elif point == CQ_DMA_END:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                elif self.state == COMPUTATION:
                    self.ticks["distance"] += time_interval
                else:
                    self.error(log_line)
                self.increase_cq_dma_counter()
            else:
                self.error(log_line)
        elif self.prev_point == COMPUTATION_END:
            assert point == GET_QUERY_VECTOR_START or           \
                   point == COMPUTATION_START or                \
                   point == COMPUTATION_END or                  \
                   point == CQ_DMA_END or                       \
                   point == POLLING_END
            if point == GET_QUERY_VECTOR_START:
                self.ticks["submission"] += time_interval
                self.increase_query_counter()
            elif point == COMPUTATION_START:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                else:
                    self.error(log_line)
                self.increase_submission_counter()
            elif point == COMPUTATION_END:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                elif self.state == COMPUTATION:
                    self.ticks["distance"] += time_interval
                else:
                    self.error(log_line)
                self.increase_computation_counter()
            elif point == CQ_DMA_END:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                elif self.state == COMPUTATION:
                    self.ticks["distance"] += time_interval
                elif self.state == CQ_DMA:
                    self.ticks["cq dma"] += time_interval
                else:
                    self.error(log_line)
                self.increase_cq_dma_counter()
            elif point == POLLING_END:
                # Some case near last this condition is satisfied
                self.ticks["cq dma"] += time_interval
            else:
                self.error(log_line)
        elif self.prev_point == CQ_DMA_END:
            assert point == QUERY_SET or                        \
                   point == DISTANCE_START or                   \
                   point == GET_QUERY_VECTOR_START or           \
                   point == COMPUTATION_START or                \
                   point == COMPUTATION_END or                  \
                   point == CQ_DMA_END or                       \
                   point == POLLING_END or                      \
                   point == DISTANCE_END or                     \
                   point == UPDATE_END or                       \
                   point == SET_END
            if point == QUERY_SET:
                self.ticks["query vector"] += time_interval
                self.ticks["query vector"] += self.tmp_tick
            elif point == DISTANCE_START:
                # Some case near last this condition is satisfied
                self.ticks["graph"] += time_interval
            elif point == GET_QUERY_VECTOR_START:
                self.ticks["submission"] += time_interval
                self.increase_query_counter()
            elif point == COMPUTATION_START:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                else:
                    self.error(log_line)
                self.increase_submission_counter()
            elif point == COMPUTATION_END:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                elif self.state == COMPUTATION:
                    self.ticks["distance"] += time_interval
                else:
                    self.error(log_line)
                self.increase_computation_counter()
            elif point == CQ_DMA_END:
                if self.state == SUBMISSION:
                    self.ticks["submission"] += time_interval
                elif self.state == QUERY:
                    self.ticks["query vector"] += time_interval
                elif self.state == COMPUTATION:
                    self.ticks["distance"] += time_interval
                elif self.state == CQ_DMA:
                    self.ticks["cq dma"] += time_interval
                else:
                    self.error(log_line)
                self.increase_cq_dma_counter()
            elif point == POLLING_END:
                if self.state == CQ_DMA:
                    # Some case near last this condition is satisfied
                    self.ticks["cq dma"] += time_interval
                elif self.state == POLLING:
                    self.ticks["polling"] += time_interval
                else:
                    self.error(log_line)
                self.state = HOST
            elif point == DISTANCE_END:
                # Some case near last this condition is satisfied
                self.ticks["accumulation"] += time_interval
            elif point == UPDATE_END:
                # Some case near last this condition is satisfied
                self.ticks["update"] += time_interval
            elif point == SET_END:
                # Some case near last this condition is satisfied
                self.ticks["update"] += time_interval
            else:
                self.error(log_line)
        elif self.prev_point == POLLING_END:
            assert point == DISTANCE_END or                     \
                   point == CQ_DMA_END
            if point == DISTANCE_END:
                self.ticks["accumulation"] += time_interval
            elif point == CQ_DMA_END:
                self.ticks["accumulation"] += time_interval
            else:
                self.error(log_line)
        elif self.prev_point == DISTANCE_END:
            assert point == CQ_DMA_END or                       \
                   point == SET_END or                          \
                   point == UPDATE_END
            if point == CQ_DMA_END:
                # Some case near last this condition is satisfied
                self.ticks["update"] += time_interval
            elif point == UPDATE_END:
                self.ticks["update"] += time_interval
            elif point == SET_END:
                self.ticks["update"] += time_interval
            else:
                self.error(log_line)
            self.reset_counter()
        elif self.prev_point == UPDATE_END:
            assert point == DISTANCE_START or                   \
                   point == CQ_DMA_END or                       \
                   point == TRAVERSE_END or                     \
                   point == SET_END
            if point == DISTANCE_START:
                self.ticks["graph"] += time_interval
            elif point == CQ_DMA_END:
                # Some case near last this condition is satisfied
                self.ticks["graph"] += time_interval
            elif point == TRAVERSE_END:
                self.ticks["graph"] += time_interval
            elif point == SET_END:
                self.ticks["update"] += time_interval
            else:
                self.error(log_line)
        elif self.prev_point == TRAVERSE_END:
            assert point == UPDATE_END or                       \
                   point == SET_END
            self.ticks["update"] += time_interval
        elif self.prev_point == SET_END:
            assert point == CQ_DMA_END
            if point == CQ_DMA_END:
                pass
            else:
                print("???")
                print(log_line)
                exit(1)

        if point == SET_END:
            self.ticks['total'] = sum(self.ticks.values())
            row_list.append(self.ticks)
            self.reset()

        self.prev_point = point
        self.prev_tick = tick


for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file != FILE:
            continue
        prev_tick = 0
        prev_point = 0
        queries = []
        for i in range(THREAD_NUM):
            queries.append([])
            for j in range(QUERY_DEPTH):
                queries[i].append(OneQuery(i, j, NDP_NUM))
        row_list = []
        output = path.split('/')[-1] + POSTFIX

        print(f'{path}/{file}')
        f = open(f'{path}/{file}')
        lines = f.read().splitlines()
        for line in lines:
            row = line.split(': ')
            tick = int(row[0])
            point = int(row[-1])
            query_index = int(row[-2])
            thread_id = int(row[-3])

            queries[thread_id][query_index].insert_tick(point, tick, line)


        df = pd.DataFrame(row_list, columns=COLUMNS).fillna(0).astype(int)
        mean = df.mean().values.tolist()
        mean = [output] + mean
        out_row_list.append(mean)

        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
        f.close()

output = DIRECTORY.split('/')[-1] + POSTFIX
print(out_row_list)
df = pd.DataFrame(out_row_list, columns=OUT_COLUMNS)
df.sort_values(["graph"],
    axis=0,
    ascending=[True],
    inplace=True)
print(df)

df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
