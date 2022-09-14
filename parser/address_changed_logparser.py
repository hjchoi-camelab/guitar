import csv
import numpy as np
import pandas as pd

f = open("/home/hjchoi/data/git/cxl-sim/m5out/simout", 'r')

result = []

COLUMNS = [
    "time", "position"
]

lines = [0, 0]
prev = 0
cur = 1
i = 0
while True:
    line = f.readline()[:-1]
    if not line:
        break
    lines[cur] = int(line.split(": ")[2], 2)

    changed_addr = lines[cur] ^ lines[prev]

    for j in range(34):
        if changed_addr % 2 == 1:
            result.append(dict(zip(COLUMNS, [i, j])))
        changed_addr = changed_addr >> 1

    prev = prev ^ 1
    cur = cur ^ 1
    i += 1

df = pd.DataFrame(result, columns=COLUMNS)
df.to_csv(f"changed_addr.csv", index=False)

f.close()
