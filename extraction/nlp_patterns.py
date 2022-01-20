"""
Extract features for one class
"""
from typing import Callable
from utils import uml
import spacy

# Helper class to get the uml result
class BuiltUML:

    def __init__(self, sentence: str) -> None:
        # load spacy
        self.nlp = spacy.load("en_core_web_sm")
        self.doc = self.nlp(sentence)

        # Start parsing
        self.matcher = spacy.matcher.DependencyMatcher(self.nlp.vocab)

        # resulting UML
        self.uml_result: uml.UML = None

    def add_rule(self, pattern_name: str, pattern: list[list[dict]], matched_action: Callable[[dict], uml.UML]):

        def store_uml_callback(matcher, doc, i, matches):

            _, token_ids = matches[i]

            current_semantics = BuiltUML.get_semantics(doc, token_ids, pattern[0])

            self.uml_result = matched_action(current_semantics)

        self.matcher.add(pattern_name, pattern, on_match=store_uml_callback)

    def parse(self, verbose: bool = True):
        matched_results = self.matcher(self.doc)
        
        if verbose:
            # Number of matches
            print(f"Matches: {len(matched_results)}")
        
        return self.uml_result

    def set_sentence(self, sentence: str):
        self.doc = self.nlp(sentence)

    def clear_rules(self):
        self.matcher = spacy.matcher.DependencyMatcher(self.nlp.vocab)

    def clear_result(self):
        self.uml_result = None

    @staticmethod
    def get_semantics(doc, token_ids, pattern):
        current_semantics = {}

        for i in range(len(token_ids)):
            matched_token = doc[token_ids[i]].text
            matched_rule = pattern[i]["RIGHT_ID"]

            current_semantics[matched_rule] = matched_token
        return current_semantics

# ------------------------------------------
# Class pattern

# copula: The ... is ...
copula_class = [
    # Pattern is: "The (subject) is a class ..."
    # Extracted info: A class with no attribute
    # anchor token: verb "to be"
    {"RIGHT_ID": "copula", "RIGHT_ATTRS": {"LEMMA": "be"}},
    # subject of the verb
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    # object of the verb
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "attr", "LEMMA": "class"},
    },
]

# Process a copula match
def process_copula_class(current_semantics: dict):

    eclass = uml.UMLClass(current_semantics["subject"].capitalize(), "class")

    package = uml.UML(eclass.name)
    package.classes.append(eclass)
    return package

# ----------------------------------------------

# Relationship pattern
relationship_pattern = [
    # Pattern is: A (noun for class A) has (numerical multiplicity) (noun for class B)
    # Extracted info: Class A has a relationship of a certain multiplicity with Class B
    # Procedure:
    # 1. use the dependency matcher for general syntax
    # 2. use the phrase matcher for multiplicities
    {"RIGHT_ID": "verb", "RIGHT_ATTRS": {"LEMMA": "have"}},
    {
        "LEFT_ID": "verb",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    {
        "LEFT_ID": "verb",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "dobj"},
    },
    {
        "LEFT_ID": "object",
        "REL_OP": ">",
        "RIGHT_ID": "number",
        "RIGHT_ATTRS": {"POS": "NUM"},
    },
]


def process_relationship_pattern(current_semantics: dict):
    source = uml.UMLClass(current_semantics["subject"].capitalize(), "rel")
    destination = uml.UMLClass(current_semantics["object"].capitalize(), "rel")

    source.association(destination)

    package = uml.UML(source.name)
    package.classes.extend([source, destination])
    return package


# Multiplicity pattern
multiplicity_terms = [
    "0 or several",
    "one and only one",
    "one or more",
    "zero or more",
    "zero or one",
    "at least one",
]