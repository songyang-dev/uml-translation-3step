"""
Extract features for one class
"""
from sys import stderr
from typing import Callable
from utils import uml
import spacy
from spacy.matcher import PhraseMatcher

# Helper class to get the uml result
class BuiltUML:
    def __init__(self, sentence: str) -> None:
        # load spacy
        self.nlp_model = spacy.load("en_core_web_sm")
        self.sentence = sentence
        self.spacy_doc = self.nlp_model(sentence)

        # Start parsing
        self.matcher = spacy.matcher.DependencyMatcher(self.nlp_model.vocab)

        # resulting UML
        self.uml_result: dict[str, uml.UML] = {}

    def add_rule(
        self,
        pattern_name: str,
        pattern: list[list[dict]],
        matched_action: Callable[[dict, "BuiltUML"], uml.UML],
    ):
        def store_uml_callback(matcher, doc, i, matches):

            _, token_ids = matches[i]

            current_semantics = BuiltUML.get_semantics(doc, token_ids, pattern[0])

            self.uml_result[pattern_name] = matched_action(current_semantics, self)

        self.matcher.add(pattern_name, pattern, on_match=store_uml_callback)

    def parse(self, verbose: bool = True):
        matched_results = self.matcher(self.spacy_doc)

        if verbose:
            # Number of matches
            print(f"Matches: {len(matched_results)}")

        return self.select_parsed_result()

    def select_parsed_result(self):
        """
        Combine all the results from the different rules together to form a fragment
        """
        if len(self.uml_result) > 0:
            return list(self.uml_result.values())[0] # placeholder
        else:
            return None


    def set_sentence(self, sentence: str):
        self.sentence
        self.spacy_doc = self.nlp_model(sentence)

    def clear_rules(self):
        self.matcher = spacy.matcher.DependencyMatcher(self.nlp_model.vocab)

    def clear_result(self):
        self.uml_result = {}

    @staticmethod
    def get_semantics(doc, token_ids, pattern):
        current_semantics = {}

        current_positions = {}

        for i in range(len(token_ids)):
            matched_token = doc[token_ids[i]].lemma_
            matched_rule = pattern[i]["RIGHT_ID"]

            current_semantics[matched_rule] = matched_token

            current_positions[matched_token] = token_ids[i]

        current_semantics["positions"] = current_positions
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
def process_copula_class(current_semantics: dict, build_in_progress: BuiltUML):

    subject : str = current_semantics["subject"]

    class_name = make_noun_pascal_case(current_semantics, build_in_progress, subject)


    eclass = uml.UMLClass(class_name, "class")

    package = uml.UML(eclass.name)
    package.classes.append(eclass)
    return package

def make_noun_pascal_case(current_semantics, build_in_progress: BuiltUML, subject: str):
    class_name = ""

    for chunk in build_in_progress.spacy_doc.noun_chunks:
        if current_semantics["positions"][subject] == chunk.root.i:
            for token in chunk:
                if token.is_stop:
                    continue
                else:
                    if token == chunk.root:
                        # remove plurals
                        class_name += token.lemma_.capitalize()
                    else:
                        class_name += token.text.capitalize()

    return class_name


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
        "RIGHT_ATTRS": {"POS": "NUM", "DEP": "nummod"},
    },
    {
        "LEFT_ID": "number",
        "REL_OP": ">",
        "RIGHT_ID": "adverb",
        "RIGHT_ATTRS": {"DEP": "advmod"}
    }
]

# Multiplicity pattern
multiplicity_conversion = {
    "0 or several": "0..*",
    "one and only one": "1..1",
    "one or more": "1..*",
    "zero or more": "0..*",
    "zero or one": "0..1",
    "at least one": "1..*",
    "exactly one": "1..1",
    "0 or more": "0..*",
    "0 or many": "0..*",
    "0 more": "0..*",
    "one or several": "1..*",
    "0 or 1": "0..1",
    "one and only": "1..1",
}


def process_relationship_pattern(current_semantics: dict, build_in_progress: BuiltUML):

    # Get classes
    source_class_name = make_noun_pascal_case(current_semantics, build_in_progress, current_semantics["subject"])
    source = uml.UMLClass(source_class_name, "rel")
    destination_class_name = make_noun_pascal_case(current_semantics, build_in_progress, current_semantics["object"])
    destination = uml.UMLClass(destination_class_name, "rel")

    # Get multiplicity
    matcher = PhraseMatcher(build_in_progress.nlp_model.vocab)
    # Only run nlp.make_doc to speed things up
    patterns = [
        build_in_progress.nlp_model.make_doc(text) for text in multiplicity_conversion.keys()
    ]
    matcher.add("Multiplicities", patterns)

    # found multiplicity
    found_multiplicity = ""

    matches = matcher(build_in_progress.spacy_doc)
    for match_id, start, end in matches:
        span = build_in_progress.spacy_doc[start:end]

        # # This would trigger if there are many matches for the multiplicity term in the sentence
        # if start != current_semantics["positions"][build_in_progress.spacy_doc[start].text]:
        #     raise Exception("Index of multiplicity does not match with dependency parse results")

        found_multiplicity = span.text

        break

    # Build UML

    try:
        source.association(destination, multiplicity_conversion[found_multiplicity])
    except KeyError:  # Unknown multiplicity
        # print(build_in_progress.spacy_doc.text, file=stderr)
        return None

    package = uml.UML(source.name)
    package.classes.extend([source, destination])
    return package
