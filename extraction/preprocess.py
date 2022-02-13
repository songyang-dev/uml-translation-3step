"""
Preprocess the data after being classified

Labels whose text is more than one sentence are separated into individual sentences.
The sentences then have all coreferences resolved.
"""

from sys import argv
from stanza.server import CoreNLPClient

if __name__ == "__main__":
    # if len(argv) != 3:
    #   print("Usage: py preprocess.py classified-data new-data")
    #   exit(1)
    text = "Chris Manning is a nice person. Chris wrote a simple sentence. He also gives oranges to people."
    with CoreNLPClient(
        annotators=[
            "tokenize",
            "ssplit",
            "pos",
            "lemma",
            "ner",
            "parse",
            "depparse",
            "coref",
        ],
        timeout=30000,
        memory="6G",
    ) as client:
        ann = client.annotate(text)


def preprocess(text: str):
    """
  Separate the given text into many sentences and resolve coreferences
  """
