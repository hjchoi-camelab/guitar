#!/usr/bin/python

############################################################
# make io latency log to cdf format
#
# "python cdf.py"
#
# input & format : set input file
# csv_dir & formatted : set output csv file
#
# input format example
#    index      latency
#    0,         73526411
#    1,         83526411
#    2,         73526411
#    3,         83526411
#
############################################################

import re
import os
import sys
import numpy as np
import numpy
import pandas as pd
import math
import glob
from bisect import bisect_left
from multiprocessing import Pool

input= sys.argv[1]
csv_format= '_cdf.csv'


def cal_cdf(data):
    sorted_data = np.sort(data)
    
    xvalues = range(0, max(data)+1)
    print(f"max xvalue: {xvalues[-1]}")
    
    yvalues = []
    data_len = sorted_data.size

    iter_xvalues = iter(xvalues)
    xvalue = next(iter_xvalues)
    for i, datum in enumerate(sorted_data):
        while xvalue < datum:
            yvalues.append(i / data_len)
            # print(f"idx: {i}, xvalue: {xvalue}, yvalue: {yvalues[-1]}, datum: {datum}")
            xvalue = next(iter_xvalues)
    yvalues.append(1)

    return xvalues, yvalues


def blktrace_latency(file):
    distance = []

    if os.path.isfile(file):
        with open(file) as f:
            num_line = 0
            for line in f:
                distance.append(int(int(line.split(",")[1]) / 1000000))
                num_line += 1

    xvalues, yvalues = cal_cdf(distance)
    df = pd.DataFrame({"distance": xvalues, "cdf": yvalues})

    print(df)

    output_file = file + csv_format

    df.to_csv(output_file, index=False)


def main():
    file = input

    blktrace_latency(file)

    # file = [input]

    # with Pool(processes=4) as pool:
    #     pool.map(blktrace_latency, file)

if __name__ == "__main__":
    main()