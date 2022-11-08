import os
import sys
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
    "interface",
    "total",
]

OUT_COLUMNS = ["type"]
OUT_COLUMNS.extend(COLUMNS)

INITIAL_VALUE = -1

SET_START = 0
QUERY_SET = (SET_START + 1)
DISTANCE_START = (QUERY_SET + 1)
COMPUTATION_START = (DISTANCE_START + 1)
COMPUTATION_END = (COMPUTATION_START + 1)
DISTANCE_END = (COMPUTATION_END + 1)
UPDATE_END = (DISTANCE_END + 1)
TRAVERSE_END = (DISTANCE_END + 1)
SET_END = (TRAVERSE_END + 1)


# global list
row_list = []
out_row_list = []


class OneQuery:
    def __init__(self, thread_id, query_index, ndp_num):
        self.thread_id = thread_id
        self.query_index = query_index
        self.ndp_num = ndp_num

        self.submission_counter = 0
        self.prev_point = INITIAL_VALUE
        self.prev_tick = INITIAL_VALUE
        self.ticks = {
            "update": 0,
            "calculation": 0,
            "graph": 0,
            "interface": 0,
            "total": 0
        }

    def reset(self):
        self.submission_counter = 0
        self.prev_tick = INITIAL_VALUE
        self.prev_point = INITIAL_VALUE
        self.ticks = {
            "update": 0,
            "calculation": 0,
            "graph": 0,
            "interface": 0,
            "total": 0
        }

    def insert_tick(self, point, tick):
        time_interval = tick - self.prev_tick

        if point == SET_START:
            pass
        elif self.prev_point == SET_START:
            assert point == QUERY_SET or                    \
                   point == DISTANCE_START
            if point == QUERY_SET:
                self.ticks["interface"] += time_interval
            elif point == DISTANCE_START:
                self.ticks["graph"] += time_interval
            else:
                print("Something wrong")
                exit(1)
        elif self.prev_point == QUERY_SET:
            assert point == DISTANCE_START
            self.ticks["graph"] += time_interval
        elif self.prev_point == UPDATE_END:
            assert point == DISTANCE_START or               \
                   point == TRAVERSE_END
            self.ticks["graph"] += time_interval
        elif self.prev_point == DISTANCE_START:
            assert point == COMPUTATION_START or            \
                   point == DISTANCE_END
            if point == COMPUTATION_START:
                self.ticks["interface"] += time_interval
                self.submission_counter += 1
            elif point == DISTANCE_END:
                self.ticks["calculation"] += time_interval
            else:
                print("Something wrong")
                exit(1)
        elif self.prev_point == COMPUTATION_START:
            assert point == COMPUTATION_START or           \
                   point == COMPUTATION_END
            if point == COMPUTATION_START:
                self.ticks["interface"] += time_interval
                self.submission_counter += 1
            elif point == COMPUTATION_END:
                if self.submission_counter == self.ndp_num:
                    self.ticks["calculation"] += time_interval
                else:
                    self.ticks["interface"] += time_interval
            else:
                print("Something wrong")
                exit(1)
        elif self.prev_point == COMPUTATION_END:
            assert point == COMPUTATION_START or            \
                   point == COMPUTATION_END or              \
                   point == DISTANCE_END
            if point == COMPUTATION_START:
                self.ticks["interface"] += time_interval
                self.submission_counter += 1
            elif point == COMPUTATION_END:
                if self.submission_counter == self.ndp_num:
                    self.ticks["calculation"] += time_interval
                else:
                    self.ticks["interface"] += time_interval
            elif point == DISTANCE_END:
                self.ticks["interface"] += time_interval
            else:
                print("Something wrong")
                exit(1)
        elif self.prev_point == DISTANCE_END:
            assert point == DISTANCE_END or                 \
                   point == UPDATE_END or                   \
                   point == SET_END
            if point == DISTANCE_END:
                self.ticks["calculation"] += time_interval
            elif point == UPDATE_END:
                self.ticks["update"] += time_interval
            elif point == SET_END:
                self.ticks["update"] += time_interval
            else:
                print("Something wrong")
                exit(1)
            self.submission_counter = 0
        elif self.prev_point == TRAVERSE_END:
            assert point == UPDATE_END or                   \
                   point == SET_END
            self.ticks["update"] += time_interval
        elif self.prev_point == SET_END:
            print("???")
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

            queries[thread_id][query_index].insert_tick(point, tick)


        df = pd.DataFrame(row_list, columns=COLUMNS).fillna(0).astype(int)
        mean = df.mean().values.tolist()
        mean = output.split('_') + mean
        out_row_list.append(mean)

        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
        f.close()

output = DIRECTORY.split('/')[-1] + POSTFIX
df = pd.DataFrame(out_row_list, columns=OUT_COLUMNS)
df.sort_values(["type"],
    axis=0,
    ascending=[True],
    inplace=True)
print(df)

df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
