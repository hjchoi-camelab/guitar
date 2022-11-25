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

# directory name: {dataset}_{search-l}_{type}_{# of the shard}
# usage "python anns_jh_data_movement_parser.py [log directory] [# of the query]"


DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]
QUERY_NUM = int(sys.argv[2])

FILE = 'debug.log'
TERMINAL_FILE = 'system.terminal'
POSTFIX = "-DATA-MOVEMENT"

TYPE_LIST = [
    'disk',
    'distributed',
    'base',
    'ndp',
    'cache',
    'nearest',
    'infinite',
]

COLUMNS = [
    "graph",
    "embedding",
    "distance",
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
OUT_COLUMNS.extend(["accuracy", "num query"])

MAGIC_WORDS = ['D', 'm5_print']

INITIAL_VALUE = -1

### point ###
DISTANCE = 'distance'
GRAPH = 'graph'
EMBEDDING = 'embedding'

class DataMovment:
    def __init__(self, type):
        self.type = type
        self.data_movement = getInitDict()


    def error(self, log_line):
        print(log_line)
        traceback.print_tb()
        exit(1)


    def add_data_size(self, point, data_size):
        self.data_movement[point] += data_size


def parsing(file_full_name):
    path = file_full_name[0]
    file = file_full_name[1]

    setting = path.split('/')[-1]
    type = setting.split('_')[-2]

    if type not in TYPE_LIST:
        print(f"wrong type: {type}")
        exit(1)


    dataset = ''
    accuracy = 0
    search_l = 0

    data_movement = DataMovment(type)

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
        if type == 'distributed':
            if magic_word != 'm5_print':
                continue
            rdma_matching = RDMA_REGEX.search(line)
            # 3.7 us per 512 bytes
            point = DISTANCE
            data_size = eval(rdma_matching.group())
        else:
            point = row[3]
            data_size = int(row[4])

        # print(line)
        data_movement.add_data_size(point, data_size)

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

    df = pd.DataFrame(data_movement.data_movement, columns=COLUMNS, index=[0]).fillna(0).astype(int)
    print(df)

    # generate mean
    mean = df.mean().values.tolist()
    mean = [dataset, search_l, type] + mean
    mean.extend([accuracy, QUERY_NUM])

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
    with Pool(1) as p:
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
