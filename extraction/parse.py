"""
Parse the English text using rules
"""
import os
import sys
from utils import uml

if len(sys.argv) != 3:
    print(
        "Usage: py parse.py kind out_file [ < pipe text through stdin ]",
        file=sys.stderr,
    )
    exit(1)

if sys.argv[1] != "class" and sys.argv[1] != "rel":
    print("Acceptable kinds are: class | rel")
    exit(1)


# ------------------------------------------------------------
# Extract features for one class

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


# ------------------------------------------------------------------
# Start parsing
from spacy_patterns import parse

out_path = sys.argv[2]

# Receives text to parse through stdin
# text = "The key to a good life is music."
text = sys.stdin.read()

if sys.argv[1] == "class":
    PACKAGE = parse(text, (sys.argv[1], [copula_class], process_copula_class))
elif sys.argv[1] == "rel":
    PACKAGE = parse(
        text, (sys.argv[1], [relationship_pattern], process_relationship_pattern)
    )

path = os.path.abspath(os.path.dirname(__file__))
PACKAGE.save(os.path.join(path, out_path))
