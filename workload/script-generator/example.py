import os
from script_generator import *

DATASET = ["sift1M"]
GRAPH_LOCATION = ["host", "cxl"]

SCRIPT_DIR = "/root/tmp/scripts"

gen = ScriptGenerator("example_template.sh")

gen.options = {"DATASET": DATASET, "GRAPH_LOCATION": GRAPH_LOCATION}

experiments, scripts = gen.generate()

for i, (exp, sc) in enumerate(zip(experiments, scripts)):
    filepath = os.path.join(SCRIPT_DIR, f"{i}.sh")

    with open(filepath, "w") as f:
        f.write(sc)

print(f"generated {len(experiments)} experiment scripts")
