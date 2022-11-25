import os
import sys
import numpy as np
import pandas as pd
from math import log

# directory name: {dataset}_{search-l}_{type}_{# of the shard}

DIRECTORY = sys.argv[1]
FILE = 'system.terminal'
POSTFIX = "-VISIT-COUNT"

COLUMNS = [
    "visit count"
]

OUT_COLUMNS = [
    "dataset",
    "search-L",
    "type",
    "# of the shard",
]
OUT_COLUMNS.extend(COLUMNS)

out_row_list = []
for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file != FILE:
            continue
        row_list = []
        setting = path.split('/')[-1]
        output = setting + POSTFIX

        print(f'{path}/{file}')
        f = open(f'{path}/{file}')
        lines = f.read().splitlines()
        for line in lines:
            if line[:5] != 'COUNT':
                continue
            if line.split(': ')[1] != "VISIT CNT":
                continue
            visit_count = [int(line.split(' ')[-1])]
            row_list.append(dict(zip(COLUMNS, visit_count)))

        df = pd.DataFrame(row_list, columns=COLUMNS).astype(int)
        mean = df.mean().values.tolist()
        mean = setting.split('_') + mean
        out_row_list.append(mean)

        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
        f.close()

output = DIRECTORY.split('/')[-1] + POSTFIX
df = pd.DataFrame(out_row_list, columns=OUT_COLUMNS)
print(df)

df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
# df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)