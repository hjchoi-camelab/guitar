import os
import sys
import numpy as np
import pandas as pd
from math import log

DIRECTORY = sys.argv[1]
FILE = 'debug.log'
POSTFIX = "-FAISS-BREAKDOWN"

DISTANCE_START = 2
SEND_DOORBELL = 10000
RECV_DOORBELL = 20000
RECV_SQ = 30000

STAGES = [
    DISTANCE_START,
    SEND_DOORBELL,
    RECV_DOORBELL,
    RECV_SQ,
]
COLUMNS = [
    "SQ set",
    "Doorbell",
    "DMA",
    "total"
]

OUT_COLUMNS = ["type"]
OUT_COLUMNS.extend(COLUMNS)

out_row_list = []
for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file != FILE:
            continue
        row_list = []
        tmp_dict = {
            DISTANCE_START: 0,
            SEND_DOORBELL: 0,
            RECV_DOORBELL: 0,
            RECV_SQ: 0,
        }
        prev_timestamp = 0
        output = path.split('/')[-1] + POSTFIX

        print(f'{path}/{file}')
        f = open(f'{path}/{file}')
        lines = f.read().splitlines()
        for line in lines:
            row = line.split(': ')
            timestamp = int(row[0])
            stage = int(row[-1])

            if stage not in STAGES:
                continue

            if stage == DISTANCE_START:
                if tmp_dict[DISTANCE_START] != 0:
                    tmp_dict = dict({
                        "SQ set": tmp_dict[SEND_DOORBELL] - tmp_dict[DISTANCE_START],
                        "Doorbell": tmp_dict[RECV_DOORBELL] - tmp_dict[SEND_DOORBELL],
                        "DMA": tmp_dict[RECV_SQ] - tmp_dict[RECV_DOORBELL],
                    })
                    tmp_dict['total'] = sum(tmp_dict.values())
                    row_list.append(tmp_dict)
                tmp_dict = {
                    DISTANCE_START: timestamp,
                    SEND_DOORBELL: 0,
                    RECV_DOORBELL: 0,
                    RECV_SQ: 0,
                }
            elif stage == SEND_DOORBELL:
                tmp_dict[SEND_DOORBELL] = timestamp
            elif stage == RECV_DOORBELL:
                tmp_dict[RECV_DOORBELL] = timestamp
            elif stage == RECV_SQ:
                tmp_dict[RECV_SQ] = timestamp

        df = pd.DataFrame(row_list, columns=COLUMNS).astype(int)
        mean = df.mean().values.tolist()
        mean = output.split('_') + mean
        out_row_list.append(mean)

        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
        f.close()

output = DIRECTORY.split('/')[-1] + POSTFIX
df = pd.DataFrame(out_row_list, columns=OUT_COLUMNS)
print(df)

df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)