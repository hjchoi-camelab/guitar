import numpy as np

f = open("/root/git/cxl-sim/m5out/simout", 'r')

cpu_results = []
bi_results = []

while True:
    line = f.readline()[:-1]
    if not line: break
    line = line.split(": ")
    
    lat = int(line[2])
    if line[1] == "system.bitest":
        bi_results.append(lat)
    else:
        cpu_results.append(lat)

bi_results = np.array(bi_results)
cpu_results = np.array(cpu_results)

print(np.sort(bi_results))
print(np.sort(cpu_results))

f.close()