import os
import numpy as np
import pandas as pd
from math import log

DIRECTORY = '/home/hjchoi/result/anns/sift1M/CXL'
FILE = 'system.terminal'

COLUMNS = [
    "pre",
    "graph",
    "distance",
    "insert",
    "mem waiting",
]

# query number
QUERY_NUMS = [
    2778,
    1748,
    1045,
    499,
    328,
    195,
]

OUT_COLUMNS = ["search_l", "memory size"]
OUT_COLUMNS.extend(COLUMNS)

out_row_list = []
for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file != FILE:
            continue
        row_list = []
        output = path.split('/')[-1]

        # query number
        query_num = QUERY_NUMS[int(log(int(output.split('_')[0]), 2)) - 4]
        cur_query = 0

        print(f'{path}/{file}')
        f = open(f'{path}/{file}')
        lines = f.read().splitlines()
        for line in lines:
            if line[:9] != "BREAKDOWN":
                continue
            row = line.split(' ')[4:]
            row_list.append(dict(zip(COLUMNS, row)))

            # query number
            cur_query += 1
            if cur_query == query_num:
                break

        df = pd.DataFrame(row_list, columns=COLUMNS).astype(int)
        mean = df.mean().values.tolist()
        mean = output.split('_') + mean
        out_row_list.append(mean)

        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
        f.close()

output = DIRECTORY.split('/')[-1]
df = pd.DataFrame(out_row_list, columns=OUT_COLUMNS)
df['search_l'] = df['search_l'].astype(int)
df.sort_values(["search_l"],
    axis=0,
    ascending=[True],
    inplace=True)
print(df)

df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)