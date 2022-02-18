"""
Preprocess the data after being classified

Labels whose text is more than one sentence are separated into individual sentences.
The sentences then have all coreferences resolved.
"""

from sys import argv

import spacy, coreferee.data_model

# import spacy

if __name__ == "__main__":
    # if len(argv) != 3:
    #     print("Usage: py preprocess.py classified-data new-data")
    #     exit(1)
    pass

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("coreferee")


def preprocess(text: str):
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

    return result


def conjunctive_addition(words: list[str]):
    """
    item1, item2, ... and last item
    """
    if len(words) == 1:
        return words[0]
    else:
        return ",".join(words[:-1]) + " and " + words[-1]


if __name__ == "__main__":

    text = "Although he was very busy with his work, Peter had had enough of it. He and his wife decided they needed a holiday. They travelled to Spain because they loved the country very much."

    result = preprocess(text)

    print(result)
