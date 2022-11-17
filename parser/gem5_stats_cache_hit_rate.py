import os
import sys
import csv
import traceback
import pdb
import re
import numpy as np
import pandas as pd
from math import log
from multiprocessing import Pool

# usage "python gem5_stats_cache_hit_rate.py [stats directory]"

DIRECTORY = sys.argv[1]
if DIRECTORY[-1] == '/':
    DIRECTORY = DIRECTORY[:-1]
NDP_NUM = int(sys.argv[2])

FILE = 'stats.txt'
POSTFIX = '-STATS'


def make_it_int(storage, output_column, value):
    storage[output_column] = int(value)


def divide_it_by_sim_ticks(storage, output_column, value):
    storage[output_column] = int(value) / storage['total ticks']


STATS = [
    {
        "name": r'finalTick',
        "callback": make_it_int,
        "output_column": 'timestamp',
        "many": False,
    }, {
        "name": r'system\.switch_cpus(\d*)\.numCycles',
        "callback": make_it_int,
        "output_column": 'CPU total cycles',
        "many": False,
    }, {
        "name": r'system\.switch_cpus(\d*)\.idleCycles',
        "callback": make_it_int,
        "output_column": 'CPU idle cycles',
        "many": False,
    }, {
        "name": r'simTicks',
        "callback": make_it_int,
        "output_column": 'total ticks',
        "many": False,
    }, {
        "name": r'system\.cxl_type3s(\d*)\.busyTick',
        "callback": divide_it_by_sim_ticks,
        "output_column": ' busy ticks',
        "many": True,
    }, {
        "name": r'system\.cxl_type3s(\d)*\.idleTick',
        "callback": divide_it_by_sim_ticks,
        "output_column": ' idle ticks',
        "many": True,
    }, {
        "name": r'system\.l2\.roiHits',
        "callback": make_it_int,
        "output_column": 'ROI hits',
        "many": False,
    }, {
        "name": r'system\.l2\.roiMisses',
        "callback": make_it_int,
        "output_column": 'ROI misses',
        "many": False,
    }, {
        "name": r'system\.l2\.roiAccesses',
        "callback": make_it_int,
        "output_column": 'ROI accesses',
        "many": False,
    },
]

def getColumns():
    columns = []
    for stat in STATS:
        if stat['many']:
            for i in range(NDP_NUM):
                output_column = str(i) + stat['output_column']
                columns.append(output_column)
        else:
            output_column = stat['output_column']
            columns.append(output_column)

    return columns


def initDict(_dict):
    for stat in STATS:
        if stat['many']:
            for i in range(NDP_NUM):
                output_column = str(i) + stat['output_column']
                _dict[output_column] = 0
        else:
            output_column = stat['output_column']
            _dict[output_column] = 0


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
                if stat['many']:
                    for i in range(NDP_NUM):
                        output_column = str(i) + stat['output_column']
                        row.append(tmp_dict[output_column])
                else:
                    output_column = stat['output_column']
                    row.append(tmp_dict[output_column])
            wr.writerow(row)
            initDict(tmp_dict)
        if line == '':
            continue

        row = line.split()
        name = row[0]

        for stat in STATS:
            m = re.match(stat['name'], name)
            if not m:
                continue

            if stat['many']:
                output_column = m.group(1) + stat['output_column']
            else:
                output_column = stat['output_column']
            value = row[1]
            stat['callback'](tmp_dict, output_column, value)
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
    with Pool(18) as p:
        p.map(parsing, file_full_names)