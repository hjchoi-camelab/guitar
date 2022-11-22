import os
import sys
from pathlib import Path

sys.path.insert(0, '../')
from script_generator import *

DATASET = ["sift10M"]
SEARCH_L = [""]
TYPE = ["distributed"]
NUM_SHARD = ["1", "2", "4", "8", "16"]

gen = ScriptGenerator(f"num_shard.sh")

gen.options = {"DATASET": DATASET, "SEARCH_L": SEARCH_L, "TYPE": TYPE, "NUM_SHARD": NUM_SHARD}

experiments, scripts = gen.generate()

for i, (exp, sc) in enumerate(zip(experiments, scripts)):
    SCRIPT_DIR = f"/root/git/guitar/workload/script-generator/scripts/distributed/"
    Path(SCRIPT_DIR).mkdir(parents=True, exist_ok=True)

    file_name = f"{exp['DATASET']}_{exp['SEARCH_L']}_{exp['TYPE']}_{exp['NUM_SHARD']}.sh"
    filepath = os.path.join(SCRIPT_DIR, file_name)
    print(filepath)

    with open(filepath, "w") as f:
        f.write(sc)

print(f"generated {len(experiments)} experiment scripts")
