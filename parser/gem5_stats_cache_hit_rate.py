import os
import sys
import csv
import traceback
import pdb
import numpy as np
import pandas as pd
from math import log
from multiprocessing import Pool

# usage "python gem5_stats_cache_hit_rate.py [stats directory]"

DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]

FILE = 'stats.txt'
POSTFIX = '-CACHE-HIT'

def makeItInt(storage, output_column, value):
    storage[output_column] = int(value)

STATS = [
    {
        "name": 'finalTick',
        "callback": makeItInt,
        "output_column": 'timestamp'
    },
    {
        "name": 'system.cpu.dcache.overallAccesses::total',
        "callback": makeItInt,
        "output_column": 'L1 accesses'
    },
    {
        "name": 'system.l2.overallAccesses::total',
        "callback": makeItInt,
        "output_column": 'L2 accesses'
    },
    {
        "name": 'system.l2.overallMisses::total',
        "callback": makeItInt,
        "output_column": 'L2 misses'
    },
    {
        "name": 'system.l2.roiHits',
        "callback": makeItInt,
        "output_column": 'ROI hits'
    },
    {
        "name": 'system.l2.roiMisses',
        "callback": makeItInt,
        "output_column": 'ROI misses'
    },
    {
        "name": 'system.l2.roiAccesses',
        "callback": makeItInt,
        "output_column": 'ROI accesses'
    },
]

def getColumns():
    columns = []
    for stat in STATS:
        columns.append(stat['output_column'])

    return columns


def initDict(_dict):
    for stat in STATS:
        _dict[stat['output_column']] = 0


def parsing(file_full_name):
    path = file_full_name[0]
    file = file_full_name[1]

    output = path.split('/')[-1] + POSTFIX
    tmp_dict = {}
    initDict(tmp_dict)
    i = 0

    print(f'{path}/{file} start')
    f = open(f'{path}/{file}')
    csv_f = open(f'{DIRECTORY}/{output}.csv', 'w', newline='')
    wr = csv.writer(csv_f)
    wr.writerow(getColumns())
    lines = f.read().splitlines()
    for line in lines:
        if line == '---------- End Simulation Statistics   ----------':
            i += 1
            if i % 1000 == 0:
                print(i)

            row = []
            for stat in STATS:
                row.append(tmp_dict[stat['output_column']])
            wr.writerow(row)
            initDict(tmp_dict)
        if line == '':
            continue

        row = line.split()
        name = row[0]

        for stat in STATS:
            if name != stat['name']:
                continue

            value = row[1]
            stat['callback'](tmp_dict, stat['output_column'], value)
            break

    f.close()
    csv_f.close()
    print(f'{path}/{file} end')


if __name__ == '__main__':
    # pool input
    file_full_names = []
    for (path, dir, files) in os.walk(DIRECTORY):
        for file in files:
            if file != FILE:
                continue
            file_full_names.append((path, file))

    # multiprocessing
    with Pool(2) as p:
        p.map(parsing, file_full_names)