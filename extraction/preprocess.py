"""
Preprocess the data after being classified

Labels whose text is more than one sentence are separated into individual sentences.
The sentences then have all coreferences resolved.
"""

from sys import argv
from stanza.server import CoreNLPClient

CLIENT: CoreNLPClient


def preprocess_start():
    """
    Starts the CoreNLP client. It takes several seconds and requires prior installation.
    """
    global CLIENT
    CLIENT = CoreNLPClient(annotators=["coref"], be_quiet=True)
    CLIENT.start()


def preprocess(text: str):
    """
    Requests the CoreNLP server. It needs to have been started.
    """
    global CLIENT
    if CLIENT is None:
        raise Exception(
            "Call preprocess_start() first. And finish with preprocess_stop()"
        )

    return CLIENT.annotate(text)


def preprocess_stop():
    """
    Stops the running CoreNLP server.
    """
    global CLIENT
    if CLIENT is None:
        raise Exception("No client started")
    CLIENT.stop()


def preprocess_once(text: str):
    """
    Separate the given text into many sentences and resolve coreferences
    """
    client = CoreNLPClient(annotators=["coref"], be_quiet=True)
    client.start()
    ann = client.annotate(text)
    client.stop()
    return ann


if __name__ == "__main__":
    # if len(argv) != 3:
    #   print("Usage: py preprocess.py classified-data new-data")
    #   exit(1)
    # text = "Chris Manning is a nice person. Chris wrote a simple sentence. He also gives oranges to people."

    text = "I have a friend named George. He is my best friend. I like him."

    preprocess_once(text)
