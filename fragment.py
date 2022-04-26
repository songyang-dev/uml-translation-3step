"""
Fragment the labeled models with the newer plantuml fragmentation algorithm
"""
import os, sys
import pandas

import fragmentation

if len(sys.argv) != 2:
    print("Usage: ./python fragment.py folder-for-output")
    exit(1)

SOURCE_DIR = "C:\\Users\\songy\\Documents\\My Documents\\UDEM\\master thesis\\uml data\\database\\analysis\\"
GROUPED_CSV_PATH = os.path.join(SOURCE_DIR, "three-step", "data", "grouped.csv")
OUT_FOLDER = sys.argv[1]

if not os.path.isfile(GROUPED_CSV_PATH):
    print("Generate the grouped.csv file through preprocess.py")
    exit(1)

os.makedirs(OUT_FOLDER, exist_ok=True)

grouped = pandas.read_csv(GROUPED_CSV_PATH)

for index, row in grouped.iterrows():
    # ignore antscript model, which is partially labeled
    model_name = row["model"]
    if model_name == "AntScripts":
        continue

    fragmentation.fragment(
        os.path.join(SOURCE_DIR, "zoo", model_name + ".plantuml"), OUT_FOLDER
    )
