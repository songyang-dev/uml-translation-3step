"""
Main script that runs the translation pipeline to get UML from English

Procedure
1. Learn the classifier
  a. Preprocess the data collected from Heroku
  b. Use Bernoulli Naive Bayes
2. Preprocess the input text into sentences
  a. Perform coreference resolution, ie. substitute pronouns
  b. Classify each sentence into "class" or "relationship"
3. Extract UML information from each sentence
  a. The rules for extraction depend on the classification result in 2b
  b. Each sentence is turned into a UML object
4. Assemble the UML model
  a. Combine all the UML objects back into one larger UML

"""

import sys

if __name__ == "__main__":
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Usage: python translate.py text [--fresh]")
        print(
            """
            This assumes that you have the Heroku training data in the parent directory.
            And you need to have installed the proper dependencies in requirements.txt. Conda activation recommended.
            """
        )
        print("text: The text you want to be turned into UML.")
        print(
            "--fresh: Whether to execute the whole pipeline again. Optimizations make the program execute partially."
        )
        exit(1)
    TEXT = sys.argv[1]
    USE_FRESH_START = True if len(sys.argv) == 2 or sys.argv[2] == "--fresh" else False

import subprocess
import os
from extraction.preprocess import resolve_coref
from classification.predict_kind import LazyLoadedClassifier
from extraction.parse import LazyLoadedExtractor


def prepare_classifier():
    if os.path.exists("data/fragment_kinds.csv") and not USE_FRESH_START:
        return
    subprocess.call(["bash", "prepare_classifier.sh", "..", "data/"])


def preprocess(text: str):
    return resolve_coref(text)


if __name__ == "__main__":
    prepare_classifier()

    # key: sentence index, item: processed text
    sentences = preprocess(TEXT)

    classifier = LazyLoadedClassifier()

    # predictions
    predicted_kinds = {}
    for sentence_id, sentence_text in sentences.items():
        predicted_kinds[sentence_id] = classifier.predict(sentence_text)

    # extraction
    extracted_umls = []

    class_extractor = LazyLoadedExtractor("", "class")
    rel_extractor = LazyLoadedExtractor("", "rel")
    for sentence_id, kind in predicted_kinds.items():
        if kind == "class":
            class_extractor.extractor.set_sentence(sentences[sentence_id])
            result = class_extractor.handle_class()
        elif kind == "rel":
            rel_extractor.extractor.set_sentence(sentences[sentence_id])
            result = rel_extractor.handle_rel()
        else:
            raise Exception("Unexpected kind!")

        if result is not None:
            extracted_umls.append(result)

    # assembly
    # TODO
    print(extracted_umls)
