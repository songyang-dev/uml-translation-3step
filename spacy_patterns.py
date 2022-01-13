"""
Handles the parsing logic
"""

from os import urandom
from struct import pack
from typing import Callable, Tuple
import uml
import spacy


def parse(
    sentence: str,
    # kind, dep patterns, matched action
    logic: Tuple[str, list[list[dict]], Callable[[dict], uml.UML]],
) -> uml.UML:

    # unpack
    kind, dependency_patterns, matched_action = logic

    # load spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(sentence)

    # Start parsing
    matcher = spacy.matcher.DependencyMatcher(nlp.vocab)

    # resulting UML
    uml_result: uml.UML = None

    def store_uml_callback(matcher, doc, i, matches):

        _, token_ids = matches[i]

        current_semantics = get_semantics(doc, token_ids, dependency_patterns.pop())

        nonlocal uml_result
        uml_result = matched_action(current_semantics)

    matcher.add(kind, dependency_patterns, on_match=store_uml_callback)

    # if kind == "class":
    #     matcher.add(kind, dependency_patterns, on_match=matched_action)
    # elif kind == "rel":
    #     matcher.add(kind, dependency_patterns, on_match=matched_action)

    matched = matcher(doc)

    print(f"Matches: {len(matched)}")

    return uml_result


def get_semantics(doc, token_ids, pattern):
    current_semantics = {}

    for i in range(len(token_ids)):
        matched_token = doc[token_ids[i]].text
        matched_rule = pattern[i]["RIGHT_ID"]

        current_semantics[matched_rule] = matched_token
    return current_semantics
