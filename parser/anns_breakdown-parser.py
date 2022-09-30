import os
import numpy as np
import pandas as pd

DIRECTORY = '/home/hjchoi/result/anns/sift1M'
FILE = 'system.terminal'

COLUMNS = [
    "pre",
    "graph",
    "distance",
    "insert",
    "llc miss",
    "mem waiting"
]

OUT_COLUMNS = ["config"].extend(COLUMNS)

out_row_list = []
for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file != "system.terminal":
            continue
        row_list = []
        output = path.split('/')[-1]
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
        mean.insert(0, output)
        out_row_list.append(dict(zip(OUT_COLUMNS, mean)))

        df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
        df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
        f.close()

output = DIRECTORY.split('/')[-1]
df = pd.DataFrame(out_row_list, columns=OUT_COLUMNS)
df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)