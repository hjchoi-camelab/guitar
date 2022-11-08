import os
import sys
import numpy as np
import pandas as pd
from math import log

DIRECTORY = sys.argv[1]
FILE = 'system.terminal'
POSTFIX = "-FAISS-BREAKDOWN"

COLUMNS = [
    "vector",
    "pre",
    "graph",
    "distance",
    "insert",
    "submission",
    "waitting4flag",
    "result"
]

OUT_COLUMNS = ["type"]
OUT_COLUMNS.extend(COLUMNS)

out_row_list = []
for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file != FILE:
            continue
        row_list = []
        output = path.split('/')[-1] + POSTFIX

        print(f'{path}/{file}')
        f = open(f'{path}/{file}')
        lines = f.read().splitlines()
        for line in lines:
            if line[:9] != "BREAKDOWN":
                continue
            row = line.split(' ')[4:]
            row_list.append(dict(zip(COLUMNS, row)))

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