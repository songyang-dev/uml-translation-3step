"""
Perform a holistic testing on the entire pipeline
"""
import os
from sys import argv
import pandas

if __name__ == "__main__":
    if len(argv) != 2:
        print("Usage: python test.py source-data-dir")
        exit(1)
    SOURCE_DIR = argv[1]


def prepare_test_set():
    """
    Creates a csv where the entries are:
    model name, labels from all fragments
    """

    LABELS = pandas.read_csv(os.path.join(SOURCE_DIR, "labels.csv"))
    FRAGMENTS = pandas.read_csv(os.path.join(SOURCE_DIR, "fragments.csv"))

    grouped: dict[str, str] = {}  # key: model name, text

    for index, row in LABELS.iterrows():
        fragment = FRAGMENTS.loc[FRAGMENTS["unique_id"] == row["fragment_id"]]

        model_name = fragment["model"].values[0]

        text: str = row["label"]

        # add punctuation
        if not text.endswith("."):
            text += "."

        if model_name in grouped:
            grouped[model_name] += " " + text
        else:
            grouped[model_name] = text

    return grouped


if __name__ == "__main__":
    grouped = prepare_test_set()

    models = []
    texts = []
    for key, item in grouped.items():
        models.append(key)
        texts.append(item)
    grouped_frame = pandas.DataFrame(data={"model": models, "text": texts})
    grouped_frame.to_csv("data/grouped.csv")
