"""
Extract features for one class
"""
from sys import stderr
from typing import Callable
from .utils import uml
import spacy
from spacy.matcher import PhraseMatcher

# Helper class to get the uml result
class BuiltUML:
    def __init__(self, sentence: str, kind: str) -> None:
        self.kind = kind

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

            result = matched_action(current_semantics, self)
            if result is not None:
                self.uml_result[pattern_name] = result

        self.matcher.add(pattern_name, pattern, on_match=store_uml_callback)

    def parse(self, verbose: bool = True):
        # clear previous results
        self.uml_result = {}

        matched_results = self.matcher(self.spacy_doc)

        if verbose:
            # Number of matches
            print(f"Matches: {len(matched_results)}")
            for match_id, _ in matched_results:
                string_id = self.nlp_model.vocab.strings[
                    match_id
                ]  # Get string representation
                print(string_id)

        return self.select_parsed_result()

    def select_parsed_result(self):
        """
        Combine all the results from the different rules together to form a fragment
        """
        if len(self.uml_result) > 0:
            found_umls: dict[str, uml.UML] = {}
            for key, value in self.uml_result.items():
                if value is None:
                    continue
                found_umls[key] = value

            if len(found_umls) == 1:
                return list(found_umls.values())[0]

            if self.kind == "class":

                if "simple copula" in found_umls:
                    return found_umls["simple copula"]
                elif "there is or exists" in found_umls:
                    return found_umls["expletive"]

                elif "3 component and clause" in found_umls:
                    return found_umls["3 component and clause"]

                elif "2 component and clause" in found_umls:
                    return found_umls["2 component and clause"]

                elif "to have" in found_umls:
                    return found_umls["to have"]

                elif "class named" in found_umls:
                    return found_umls["class named"]

                elif "compound" in found_umls:
                    return found_umls["compound"]

                elif "compound class explicit" in found_umls:
                    return found_umls["compound class explicit"]

                elif "component of package" in found_umls:
                    return found_umls["component of package"]

            elif self.kind == "rel":

                if "to have with multiplicity" in found_umls:
                    return found_umls["to have with multiplicity"]

                elif "to have" in found_umls:
                    return found_umls["to have"]

                elif "composed" in found_umls:  # this might be changed to gain priority
                    return found_umls["composed"]

                elif "noun with" in found_umls:
                    return found_umls["noun with"]

                elif "passive voice" in found_umls:
                    return found_umls["passive voice"]

                elif "active voice" in found_umls:
                    return found_umls["active voice"]

                elif "copula rel" in found_umls:
                    return found_umls["copula rel"]

        else:
            return None

    def set_sentence(self, sentence: str):
        self.sentence = sentence
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

# copula: The ... is a class ...
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
    """
    current_semantics is a dictionary where the keys are the left-ids of the dep pattern
    and the values are the word captured by the pattern
    """

    subject: str = current_semantics["subject"]

    class_name = make_noun_pascal_case(current_semantics, build_in_progress, subject)

    eclass = uml.UMLClass(class_name, "class")

    package = uml.UML(eclass.name)
    package.classes.append(eclass)
    return package


def make_noun_pascal_case(current_semantics, build_in_progress: BuiltUML, noun: str):
    class_name = ""

    noun_token = build_in_progress.spacy_doc[current_semantics["positions"][noun]]

    for chunk in build_in_progress.spacy_doc.noun_chunks:
        if noun_token == chunk.root:
            for token in chunk:
                if token.is_stop:
                    continue
                elif token.text == "exactly":
                    continue
                else:
                    if token.text.isupper():  # acronym case
                        class_name += token.text
                        continue

                    if token == chunk.root:
                        # remove plurals
                        class_name += token.lemma_.capitalize()
                    else:
                        class_name += token.text.capitalize()

    # in case the spacy model's noun chunks are wrong!
    if class_name == "":
        if noun_token.text.isupper():
            return noun_token.text
        return noun_token.lemma_.capitalize()
    return class_name


# expletive: There is / exists ...
expletive = [
    # Pattern is: There is / exists (noun for class).
    # Extracted info: An empty class with the name of the noun
    {"RIGHT_ID": "copula", "RIGHT_ATTRS": {"LEMMA": {"IN": ["be", "exist"]}}},
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "expl"},
    },
    # object of the verb
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {
            "DEP": {"IN": ["attr", "npadvmod", "dobj"]},
            "POS": {"IN": ["NOUN", "PROPN"]},
        },
    },
]


def process_expletive(current_semantics: dict, build_in_progress: BuiltUML):

    # Get class
    class_name = make_noun_pascal_case(
        current_semantics, build_in_progress, current_semantics["object"]
    )

    eclass = uml.UMLClass(class_name, "class")
    package = uml.UML(eclass.name)
    package.classes.append(eclass)
    return package


# general compound noun: The drawing interface format.
compound = [
    # Pattern is: (anything compound) (Proper Noun, can't be "class")
    # Extracted info: An empty class with the noun as the name.
    {
        "RIGHT_ID": "noun",
        "RIGHT_ATTRS": {
            "POS": {"IN": ["PROPN", "NOUN"]},
            "LEMMA": {"NOT_IN": ["class", "Class"]},
            "DEP": "ROOT",
        },
    }
]


def process_compound(current_semantics: dict, build: BuiltUML):
    # reject multi-sentences
    if len(list(build.spacy_doc.sents)) > 1:
        return None

    noun_token = build.spacy_doc[
        current_semantics["positions"][current_semantics["noun"]]
    ]

    class_name = make_noun_pascal_case(current_semantics, build, noun_token.lemma_)
    eclass = uml.UMLClass(class_name, "class")
    package = uml.UML(eclass.name)
    package.classes.append(eclass)
    return package


# noun sentences with the class mention
compound_class_explicit = [
    # Pattern: (anything compound) class
    # Extracted: Empty class with the name of the compound
    {
        "RIGHT_ID": "noun",
        "RIGHT_ATTRS": {
            "POS": {"IN": ["PROPN", "NOUN"]},
            "LEMMA": {"IN": ["class", "Class"]},
            "DEP": "ROOT",
        },
    },
    {
        "LEFT_ID": "noun",
        "REL_OP": ">",
        "RIGHT_ID": "complement",
        "RIGHT_ATTRS": {"DEP": {"IN": ["amod", "compound"]}},
    },
]


def process_compound_class_explicit(current_semantics: dict, build: BuiltUML):
    # reject multi-sentences
    if len(list(build.spacy_doc.sents)) > 1:
        return None

    noun_token = build.spacy_doc[
        current_semantics["positions"][current_semantics["noun"]]
    ]

    chunks = list(build.spacy_doc.noun_chunks)

    if len(chunks) > 1:
        return None
    chunk = chunks[0]
    if chunk.root != noun_token:
        return None

    class_name = ""
    for word in chunk:
        if word.is_stop:
            continue
        if word == noun_token:  # the "class" word
            continue
        if word.text.isupper():  # an acronym
            class_name += word.text
        else:
            class_name += word.lemma_.capitalize()

    if class_name == "":
        return None

    eclass = uml.UMLClass(class_name, "class")
    package = uml.UML(eclass.name)
    package.classes.append(eclass)
    return package


# to have. This pattern catches too many false positives and loses information that can be
# extracted by more detailed patterns.
class_to_have = [
    # Pattern: (subject) has/contains/includes/comprise (object)
    # Extracted info: Class with one untyped attribute
    {
        "RIGHT_ID": "have",
        "RIGHT_ATTRS": {
            "DEP": "ROOT",
            "POS": "VERB",
            "LEMMA": {"IN": ["have", "contain", "include", "comprise"]},
        },
    },
    {
        "LEFT_ID": "have",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    {
        "LEFT_ID": "have",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "dobj"},
    },
]


def process_class_to_have(current_semantics: dict, build: BuiltUML):
    class_name = make_noun_pascal_case(
        current_semantics, build, current_semantics["subject"]
    )
    attribute_name = make_noun_camel_case(
        current_semantics, build, current_semantics["object"]
    )

    eclass = uml.UMLClass(class_name, "class")
    eclass.attribute(attribute_name, attribute_type=None)
    package = uml.UML(eclass.name)
    package.classes.append(eclass)
    return package


def make_noun_camel_case(current_semantics: dict, build: BuiltUML, noun: str):
    class_name = ""

    noun_token = build.spacy_doc[current_semantics["positions"][noun]]

    tokens: list[str] = []

    for chunk in build.spacy_doc.noun_chunks:
        if noun_token != chunk.root:
            continue

        for word in chunk:

            if word.is_stop:
                continue

            if word.is_upper:  # acronym
                tokens.append(word.text)
            else:
                tokens.append(word.lemma_)

    if len(tokens) == 0:
        if noun_token.is_upper:
            return noun_token.text
        else:
            return noun

    for i, token in enumerate(tokens):
        if i == 0:
            class_name += token
            continue
        class_name += token.capitalize()

    return class_name


# class named
class_named = [
    # Pattern: A class named (object of a participle)
    # Extracted info: Empty class object as the name
    {
        "RIGHT_ID": "class",
        "RIGHT_ATTRS": {"LEMMA": {"IN": ["class", "Class"]}, "DEP": "ROOT"},
    },
    {
        "LEFT_ID": "class",
        "REL_OP": ">",
        "RIGHT_ID": "named",
        "RIGHT_ATTRS": {"POS": "VERB", "LEMMA": "name"},
    },
    {
        "LEFT_ID": "named",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "oprd"},
    },
]


def process_class_named(semantics: dict, build: BuiltUML):
    class_name = make_noun_pascal_case(semantics, build, semantics["object"])

    eclass = uml.UMLClass(class_name, "class")
    package = uml.UML(eclass)
    package.classes.append(eclass)
    return package


# component of a package
component_package = [
    # Pattern: (subject) is a component/part of the package ...
    # Extracted: Empty class of that name
    {"RIGHT_ID": "copula", "RIGHT_ATTRS": {"LEMMA": "be", "DEP": "ROOT"}},
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "component",
        "RIGHT_ATTRS": {"DEP": "attr", "LEMMA": {"IN": ["component", "part"]}},
    },
    {
        "LEFT_ID": "component",
        "REL_OP": ">>",
        "RIGHT_ID": "package",
        "RIGHT_ATTRS": {"LEMMA": "package"},
    },
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
]


def process_component_package(semantics: dict, build: BuiltUML):
    class_name = make_noun_pascal_case(semantics, build, semantics["subject"])

    eclass = uml.UMLClass(class_name, "class")
    package = uml.UML(eclass)
    package.classes.append(eclass)
    return package


# to have X, Y, ... and Z
class_to_have_and_many_clauses = [
    # Pattern: (subject) has/includes/... (object 1), (object 2) ... and (object n)
    # Extraction: class with name that has many attributes
    {
        "RIGHT_ID": "have",
        "RIGHT_ATTRS": {
            "DEP": "ROOT",
            "LEMMA": {"IN": ["have", "contain", "include", "comprise"]},
        },
    },
    {
        "LEFT_ID": "have",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    {
        "LEFT_ID": "have",
        "REL_OP": ">",
        "RIGHT_ID": "first object",
        "RIGHT_ATTRS": {"DEP": "dobj"},
    },
    {
        "LEFT_ID": "first object",
        "REL_OP": ">",
        "RIGHT_ID": "second object",
        "RIGHT_ATTRS": {"DEP": "appos"},
    },
    {
        "LEFT_ID": "second object",
        "REL_OP": ">",
        "RIGHT_ID": "and",
        "RIGHT_ATTRS": {"DEP": "cc", "LEMMA": "and"},
    },
    {
        "LEFT_ID": "second object",
        "REL_OP": ">",
        "RIGHT_ID": "last object",
        "RIGHT_ATTRS": {"DEP": "conj"},
    },
]


def process_class_to_have_and_many_clauses(semantics: dict, build: BuiltUML):
    class_name = make_noun_pascal_case(semantics, build, semantics["subject"])

    object1_name = make_noun_pascal_case(semantics, build, semantics["first object"])
    object2_name = make_noun_pascal_case(semantics, build, semantics["second object"])
    object3_name = make_noun_pascal_case(semantics, build, semantics["last object"])

    eclass = uml.UMLClass(class_name, "class")
    package = uml.UML(eclass)

    eclass.attribute(object1_name, "")
    eclass.attribute(object2_name, "")
    eclass.attribute(object3_name, "")

    package.classes.append(eclass)
    return package


class_to_have_and_clause = [
    # Pattern: (subject) has/includes/... (object 1) and (object 2)
    # Extraction: class with name that has many attributes
    {
        "RIGHT_ID": "have",
        "RIGHT_ATTRS": {
            "DEP": "ROOT",
            "LEMMA": {"IN": ["have", "contain", "include", "comprise"]},
        },
    },
    {
        "LEFT_ID": "have",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    {
        "LEFT_ID": "have",
        "REL_OP": ">",
        "RIGHT_ID": "first object",
        "RIGHT_ATTRS": {"DEP": "dobj"},
    },
    {
        "LEFT_ID": "first object",
        "REL_OP": ">",
        "RIGHT_ID": "and",
        "RIGHT_ATTRS": {"DEP": "cc", "LEMMA": "and"},
    },
    {
        "LEFT_ID": "first object",
        "REL_OP": ">",
        "RIGHT_ID": "last object",
        "RIGHT_ATTRS": {"DEP": "conj"},
    },
]


def process_class_to_have_and_clause(semantics: dict, build: BuiltUML):
    class_name = make_noun_pascal_case(semantics, build, semantics["subject"])

    object1_name = make_noun_pascal_case(semantics, build, semantics["first object"])
    object2_name = make_noun_pascal_case(semantics, build, semantics["last object"])

    eclass = uml.UMLClass(class_name, "class")
    package = uml.UML(eclass)

    eclass.attribute(object1_name, "")
    eclass.attribute(object2_name, "")

    package.classes.append(eclass)
    return package


# ----------------------------------------------

# Relationship pattern

# simple to have
rel_to_have = [
    # Pattern: (subject) has (object)
    # Extracted: Two classes with an unnamed association from subject to object
    {
        "RIGHT_ID": "have",
        "RIGHT_ATTRS": {
            "DEP": "ROOT",
            "POS": "VERB",
            "LEMMA": {"IN": ["have", "contain"]},
        },
    },
    {
        "LEFT_ID": "have",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    {
        "LEFT_ID": "have",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "dobj"},
    },
]


def process_rel_to_have(semantics: dict, build: BuiltUML):
    source_class = make_noun_pascal_case(semantics, build, semantics["subject"])
    dest_class = make_noun_pascal_case(semantics, build, semantics["object"])

    source_eclass = uml.UMLClass(source_class, "rel")
    dest_eclass = uml.UMLClass(dest_class, "rel")

    source_eclass.association(dest_eclass, "", "")

    package = uml.UML(source_eclass.name)
    package.classes.extend([source_eclass, dest_eclass])
    return package


# to have with multiplicity check
rel_to_have_multiplicity = [
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
        "RIGHT_ATTRS": {"DEP": "advmod"},
    },
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


def process_rel_to_have_multiplicity(
    current_semantics: dict, build_in_progress: BuiltUML
):

    # Get classes
    source_class_name = make_noun_pascal_case(
        current_semantics, build_in_progress, current_semantics["subject"]
    )
    source = uml.UMLClass(source_class_name, "rel")
    destination_class_name = make_noun_pascal_case(
        current_semantics, build_in_progress, current_semantics["object"]
    )
    destination = uml.UMLClass(destination_class_name, "rel")

    found_multiplicity = extract_multiplicity(current_semantics, build_in_progress)

    # Build UML

    source.association(destination, multiplicity_conversion[found_multiplicity])

    package = uml.UML(source.name)
    package.classes.extend([source, destination])
    return package


def extract_multiplicity(current_semantics, build_in_progress):
    # Get multiplicity
    matcher = PhraseMatcher(build_in_progress.nlp_model.vocab)
    # Only run nlp.make_doc to speed things up
    patterns = [
        build_in_progress.nlp_model.make_doc(text)
        for text in multiplicity_conversion.keys()
    ]
    matcher.add("Multiplicities", patterns)

    # found multiplicity
    found_multiplicity = ""

    matches = matcher(build_in_progress.spacy_doc)
    for match_id, start, end in matches:
        span = build_in_progress.spacy_doc[start:end]

        # This would trigger if there are many matches for the multiplicity term in the sentence
        if not (
            start <= current_semantics["positions"][current_semantics["adverb"]] <= end
        ):
            print(
                build_in_progress.sentence,
                "This sentence has many multiplicities. Confusing.",
                file=stderr,
            )

        found_multiplicity = span.text

        break
    return found_multiplicity


# Passive voice
passive_voice = [
    # Pattern: (subject) is (verb in passive voice) by (object)
    # Extracted: Two classes with a relationship of the verb between them.
    # The relationship is the indicative of the verb.
    # object -> (verb in active form) -> subject
    {"RIGHT_ID": "verb", "RIGHT_ATTRS": {"DEP": "ROOT", "POS": "VERB"}},
    {
        "LEFT_ID": "verb",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {
            "DEP": "nsubjpass",
            "POS": {"IN": ["NOUN", "PROPN"]},
        },  # simple passive voice
    },
    {
        "LEFT_ID": "verb",
        "REL_OP": ">",
        "RIGHT_ID": "by",
        "RIGHT_ATTRS": {"POS": "ADP"},
    },
    {
        "LEFT_ID": "by",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "pobj", "POS": {"IN": ["NOUN", "PROPN"]}},
    },
]


def process_passive_voice(semantics: dict, build: BuiltUML):
    source_class = make_noun_pascal_case(semantics, build, semantics["object"])
    dest_class = make_noun_pascal_case(semantics, build, semantics["subject"])

    source_eclass = uml.UMLClass(source_class, "rel")
    dest_eclass = uml.UMLClass(dest_class, "rel")

    association_name = semantics["verb"]  # must change this from verb to noun

    source_eclass.association(dest_eclass, "", association_name)

    package = uml.UML(source_eclass.name)
    package.classes.extend([source_eclass, dest_eclass])
    return package


# Composition
composed = [
    # Pattern: (subject) is composed/associated ... (object)
    # Extracted: Two classes with a relation from subject to object
    {
        "RIGHT_ID": "composed",
        "RIGHT_ATTRS": {"LEMMA": {"IN": ["compose", "associate"]}, "DEP": "ROOT"},
    },
    {
        "LEFT_ID": "composed",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubjpass"},
    },
    {
        "LEFT_ID": "composed",
        "REL_OP": ">>",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"POS": {"IN": ["PROPN", "NOUN"]}},
    },
]


def process_composed(semantics: dict, build: BuiltUML):
    source_name = make_noun_pascal_case(semantics, build, semantics["subject"])
    dest_name = make_noun_pascal_case(semantics, build, semantics["object"])

    source_eclass = uml.UMLClass(source_name, "rel")
    dest_eclass = uml.UMLClass(dest_name, "rel")

    source_eclass.association(dest_eclass, "", "")

    package = uml.UML(source_eclass.name)
    package.classes.extend([source_eclass, dest_eclass])
    return package


# Active voice
active_voice = [
    # Pattern: (subject) (verb in active voice, except some) (object)
    # Extracted: Two classes with a named relation
    {
        "RIGHT_ID": "verb",
        "RIGHT_ATTRS": {"LEMMA": {"NOT_IN": ["be", "exist"]}, "DEP": "ROOT"},
    },
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
]


def process_active_voice(semantics: dict, build: BuiltUML):
    source_name = make_noun_pascal_case(semantics, build, semantics["subject"])
    dest_name = make_noun_pascal_case(semantics, build, semantics["object"])

    rel_name = semantics["verb"]

    source_eclass = uml.UMLClass(source_name, "rel")
    dest_eclass = uml.UMLClass(dest_name, "rel")

    source_eclass.association(dest_eclass, multiplicity="", name=rel_name)

    package = uml.UML(source_eclass.name)
    package.classes.extend([source_eclass, dest_eclass])
    return package


# Active voice with prepositional verbs
active_voice_preposition = [
    # Pattern: (subject) (prepositional verb in active voice, except some) (object)
    # Extracted: Two classes with a named relation
    {
        "RIGHT_ID": "verb",
        "RIGHT_ATTRS": {"DEP": "ROOT", "LEMMA": {"NOT_IN": ["be", "exist"]}},
    },
    {
        "LEFT_ID": "verb",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    {
        "LEFT_ID": "verb",
        "REL_OP": ">>",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "pobj"},
    },
]


def process_active_voice_preposition(semantics: dict, build: BuiltUML):
    return process_active_voice(semantics, build)


# Simple with
noun_with = [
    # Pattern: (noun) with (noun)
    # Extracted: Two classes with a relation
    {
        "RIGHT_ID": "noun",
        "RIGHT_ATTRS": {"POS": {"IN": ["PROPN", "NOUN"]}, "DEP": "ROOT"},
    },
    {
        "LEFT_ID": "noun",
        "REL_OP": ">",
        "RIGHT_ID": "with",
        "RIGHT_ATTRS": {"POS": "ADP", "DEP": "prep", "LEMMA": "with"},
    },
    {
        "LEFT_ID": "with",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"POS": {"IN": ["PROPN", "NOUN"]}, "DEP": "pobj"},
    },
]


def process_noun_with(semantics: dict, build: BuiltUML):
    source_name = make_noun_pascal_case(semantics, build, semantics["noun"])
    dest_name = make_noun_pascal_case(semantics, build, semantics["object"])

    source_eclass = uml.UMLClass(source_name, "rel")
    dest_eclass = uml.UMLClass(dest_name, "rel")

    source_eclass.association(dest_eclass, multiplicity="", name="")

    package = uml.UML(source_eclass.name)
    package.classes.extend([source_eclass, dest_eclass])
    return package


# copula + prep
copula_rel = [
    # Pattern: (subject) is (complement) of/in (noun)
    # Extracted: Subject class is pointed to by a noun class with a complement
    # name for the relation.
    {"RIGHT_ID": "copula", "RIGHT_ATTRS": {"LEMMA": "be", "DEP": "ROOT"}},
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "complement",
        "RIGHT_ATTRS": {"DEP": "attr"},
    },
    {
        "LEFT_ID": "complement",
        "REL_OP": ">",
        "RIGHT_ID": "prep",
        "RIGHT_ATTRS": {"POS": "ADP"},
    },
    {
        "LEFT_ID": "prep",
        "REL_OP": ">",
        "RIGHT_ID": "noun",
        "RIGHT_ATTRS": {"DEP": "pobj"},
    },
]


def process_copula_rel(semantics: dict, build: BuiltUML):
    source_name = make_noun_pascal_case(semantics, build, semantics["noun"])
    dest_name = make_noun_pascal_case(semantics, build, semantics["subject"])

    source_eclass = uml.UMLClass(source_name, "rel")
    dest_eclass = uml.UMLClass(dest_name, "rel")

    source_eclass.association(
        dest_eclass, multiplicity="", name=semantics["complement"]
    )

    package = uml.UML(source_eclass.name)
    package.classes.extend([source_eclass, dest_eclass])
    return package

