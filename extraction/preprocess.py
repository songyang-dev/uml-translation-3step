"""
Preprocess the data after being classified

Labels whose text is more than one sentence are separated into individual sentences.
The sentences then have all coreferences resolved.
"""

import sys
import os

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: py preprocess.py classified-data new-data")
        exit(1)
    CLASSIFIED = os.path.join(os.getcwd(), sys.argv[1])
    OUTPUT = os.path.join(os.getcwd(), sys.argv[2])

import pickle
from numpy import nan
import spacy, coreferee.data_model


nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("coreferee")


def resolve_coref(text: str):
    """
    Substitute all the coreferences. Then split the sentences.
    """
    doc = nlp(text)

    chains: coreferee.data_model.ChainHolder = doc._.coref_chains

    substitutions = {}

    for chain in chains:
        chain: coreferee.data_model.Chain
        most_specific_mention = chain[chain.most_specific_mention_index]
        for mention in chain:
            mention: coreferee.data_model.Mention

            # the original mention
            if mention == most_specific_mention:
                continue

            # do not substitute possessive articles his, her, its
            if doc[mention.root_index].text in ["his", "her", "its"]:
                continue

            # record changes of all mentions to be the most specific one
            # root, (source indexes, new indexes)
            substitutions[mention.root_index] = (
                mention.token_indexes,
                most_specific_mention.token_indexes,
            )

    # perform substitutions
    result = {0: ""}  # sentence id, sentence str
    carry_over = {}  # token id, replacement str
    sent_id = 0  # current sentence

    # cycle through the original text
    for token in doc:

        # there is a substitution
        if token.i in substitutions:
            to_be_replaced, replacement = substitutions[token.i]
            if len(to_be_replaced) > 1:
                # add other indices to be carried over
                for extra_id in to_be_replaced[1:]:
                    carry_over[extra_id] = conjunctive_addition(
                        [doc[w].text for w in replacement]
                    )

            if len(to_be_replaced) == 0:
                raise Exception("No source tokens for substitution")

            result[sent_id] += conjunctive_addition([doc[w].text for w in replacement])
            result[sent_id] += " "

        # carry over substitution
        elif token.i in carry_over:
            result[sent_id] += carry_over[token.i]

        # no substitution
        else:
            result[sent_id] += token.text
            result[sent_id] += " "

        # next sentence
        if token.is_sent_end:
            sent_id += 1
            result[sent_id] = ""

    for key, item in result.items():
        result[key] = result[key].strip()
    del result[sent_id]

    return result


def conjunctive_addition(words: list[str]):
    """
    item1, item2, ... and last item
    """
    if len(words) == 1:
        return words[0]
    else:
        return ",".join(words[:-1]) + " and " + words[-1]


class LazyLoadedClassifier:
    def __init__(self) -> None:
        self.is_loaded = False
        self.model = None
        self.vec = None

    def predict(self, text: str):

        path = os.path.abspath(os.path.dirname(__file__))

        if self.is_loaded:
            model = self.model
            vec = self.vec
        else:
            model = pickle.load(
                open(os.path.join(path, "../classification/bernoulliNB.pickle"), "rb")
            )
            vec = pickle.load(
                open(os.path.join(path, "../classification/tfidf.vec"), "rb")
            )

        return model.predict(vec.transform([text]))[0]


if __name__ == "__main__":

    import pandas
    import os

    # Read data
    # Resolve corefs
    # Predict the kind of these new fragments
    # Write a new dataset

    CLASSIFIED = pandas.read_csv(
        os.path.join(os.getcwd(), CLASSIFIED), header=0, index_col=0
    )

    # each list will be a dataframe column
    processed_index = []
    processed_text = []
    processed_kind = []
    processed_offset = []  # nan if the fragment is just one sentence during coref

    # Import a trained classifier
    kind_predictor = LazyLoadedClassifier()

    for index, fragment in CLASSIFIED.iterrows():
        text = fragment["english"]
        kind = fragment["kind"]

        # keys are sentence index, items are sentences
        resolution = resolve_coref(text)

        if len(resolution) == 1:
            processed_index.append(index)
            processed_text.append(text)
            processed_kind.append(kind)
            processed_offset.append(nan)

        else:
            # perform predictions
            for sentence_id, sentence_text in resolution.items():
                processed_index.append(index)
                processed_text.append(sentence_text)
                processed_kind.append(kind_predictor.predict(sentence_text))
                processed_offset.append(sentence_id)

    new_data = pandas.DataFrame(
        data={
            "original label index": processed_index,
            "english": processed_text,
            "kind": processed_kind,
            "offset": processed_offset,
        }
    )
    new_data.to_csv(OUTPUT)

