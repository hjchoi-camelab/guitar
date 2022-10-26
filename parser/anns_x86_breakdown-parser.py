import os
import numpy as np
import pandas as pd

DIRECTORY = '/root/git/anns/faiss-experiments/results/test'
FILE = 'sift1M'

COLUMNS = [
    "pre",
    "graph",
    "distance",
    "insert",
    "llc miss",
    "mem waiting"
]

OUT_COLUMNS = ["config"]
OUT_COLUMNS.extend(COLUMNS)

row_list_dict = {}
out_row_list = []

f = open(f'{DIRECTORY}/{FILE}')
lines = f.read().splitlines()
for line in lines:
    if line[:9] != "BREAKDOWN":
        continue
    search_l = line.split(' ')[2]
    row = line.split(' ')[4:]
    if search_l not in row_list_dict:
        row_list_dict[search_l] = []
    row_list_dict[search_l].append(dict(zip(COLUMNS, row)))

for search_l in row_list_dict:
    output = search_l
    print(output)
    row_list = row_list_dict[search_l]
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