# Preprocess the data for use

# Algorithm
# 1. Classification of the kind of fragment
# 2. Syntax parsing and use of heuristics to populate templates
# 3. Assembly of fragments into one model

# Here, we do step 0: preprocessing

# Command line
import os
import sys

if len(sys.argv) != 3:
    print("Usage: python preprocess.py source-dir destination-dir", file=sys.stderr)
    exit(1)

# Read data from csv into another
# FORMAT: "text text text", kind
# kind = class | rel

import pandas as pd


def preprocess(source_dir: str, destination_dir: str):

    labels = pd.read_csv(os.path.join(source_dir, "labels.csv"))
    fragments = pd.read_csv(os.path.join(source_dir, "fragments.csv"))

    paired_index = []
    paired_labels = []
    paired_kind = []

    # sort fragments according to id
    # id starts at 1
    fragments.sort_values(by=["unique_id"], inplace=True)

    # iterate through labels
    for index, label in labels.iterrows():
        paired_index.append(label["id"])

        tokenize = label["label"]

        paired_labels.append(tokenize)

        fragment = fragments.iloc[label["fragment_id"] - 1]

        # open fragment plantuml code
        kind = fragment["kind"]

        paired_kind.append(kind)

    # output
    paired = pd.DataFrame(
        data={"english": paired_labels, "kind": paired_kind}, index=paired_index
    )
    os.makedirs(destination_dir, exist_ok=True)
    paired.to_csv(os.path.join(destination_dir, "fragment_kinds.csv"))


preprocess(sys.argv[1], sys.argv[2])
