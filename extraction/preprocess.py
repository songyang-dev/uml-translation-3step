"""
Preprocess the data after being classified

Labels whose text is more than one sentence are separated into individual sentences.
The sentences then have all coreferences resolved.
"""

from sys import argv

# import spacy, coreferee
import spacy

if __name__ == "__main__":
    # if len(argv) != 3:
    #     print("Usage: py preprocess.py classified-data new-data")
    #     exit(1)
    pass

nlp = spacy.load("en_core_web_sm")
# nlp.add_pipe("coreferee")


def preprocess(text: str):
    """
    Substitute all the coreferences. Then split the sentences.
    """
    doc = nlp(text)
    for s in doc.sents:
        print(s)


if __name__ == "__main__":

    text = "Although he was very busy with his work, Peter had had enough of it. He and his wife decided they needed a holiday. They travelled to Spain because they loved the country very much."

    result = preprocess(text)

    print(result)
