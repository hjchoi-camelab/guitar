from itertools import combinations
import random

items = [
  "429.mcf",
  "433.milc",
  "434.zeusmp",
  "437.leslie3d",
  "445.gobmk",
  "453.povray",
  "459.GemsFDTD",
  "470.lbm",
  "471.omnetpp",
]

SPECDIR="/root/speccpu"

combs = list(combinations(items, 4))

for comb in combs:
    filename = '-'.join(comb)
    f = open(f'/home/hjchoi/git/cxl-sim/script/multi/{filename}.sh', 'w')
    f.write('set -x\n')
    for i, workload in enumerate(comb):
        f.write(f'cd {SPECDIR}/{workload}\n')
        if i == len(comb)-1:
            f.write(f'{SPECDIR}/{workload}/run.sh && m5 exit\n')
        else:
            f.write(f'{{ {SPECDIR}/{workload}/run.sh; m5 exit; }} &\n')
    f.close()
    if random.randint(1, 6) != 6:
        continue
    print(filename)


##################
# OUTPUT EXAMPLE #
##################
# set -x
# cd /root/speccpu/429.mcf
# { /root/speccpu/429.mcf/run.sh; m5 exit; } &
# cd /root/speccpu/433.milc
# { /root/speccpu/433.milc/run.sh; m5 exit; } &
# cd /root/speccpu/434.zeusmp
# { /root/speccpu/434.zeusmp/run.sh; m5 exit; } &
# cd /root/speccpu/453.povray
# /root/speccpu/453.povray/run.sh && m5 exit