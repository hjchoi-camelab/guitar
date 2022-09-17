import csv

f = open("/home/hjchoi/data/git/cxl-sim/m5out/simout", 'r')
csv_f = open("/home/hjchoi/data/changed_addr.csv", 'w', newline='')
wr = csv.writer(csv_f)

result = []

COLUMNS = [
    "time", "position"
]

wr.writerow(COLUMNS)

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
            wr.writerow(([i, j]))
        changed_addr = changed_addr >> 1

    prev = prev ^ 1
    cur = cur ^ 1
    i += 1

f.close()
csv_f.close()