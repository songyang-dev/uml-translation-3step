# Parse the English text using rules

import sys
from numpy import string_
if len(sys.argv) != 3:
    print(
        "Usage: py parse.py kind out_file [ < pipe text through stdin ]", file=sys.stderr)
    exit(1)

if sys.argv[1] != "class" and sys.argv[1] != "rel":
    print("Acceptable kinds are: class | rel")
    exit(1)

from spacy.matcher import DependencyMatcher
import spacy

out_path = sys.argv[2]

# Receives text to parse through stdin
# text = "The key to a good life is music."
text = sys.stdin.read()


nlp = spacy.load("en_core_web_sm")
doc = nlp(text)


# Extract features for one class

# copula: The ... is ...
copula_class = [
    # Pattern is: "The Monochrome is a class in the ... package."
    # Extracted info: A class with no attribute

    # anchor token: verb "to be"
    {
        "RIGHT_ID": "copula",
        "RIGHT_ATTRS": {"LEMMA": "be"}
    },
    # subject of the verb
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"}
    },
    # object of the verb
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "attr", "LEMMA": "class"}
    }
]

# Relationship pattern


# Abstract representation of a UML model
import ecore
from pyecore.ecore import EString

leading_class_name = ""
uml_classes = []

def on_match(matcher, doc, i, matches):

    match_id, _ = matches[i]
    string_id = nlp.vocab.strings[match_id]

    if string_id == "copula class":
        process_copula_class(doc, matches[i])

    elif string_id == "REL":
        process_relationship(doc, matches[i])

# Process a copula match
def process_copula_class(doc, m):
    _, token_ids = m

    current_semantics = {}

    for i in range(len(token_ids)):
        matched_token = doc[token_ids[i]].text
        matched_rule = copula_class[i]["RIGHT_ID"]

        current_semantics[matched_rule] = matched_token

    eclass = ecore.declare_class(current_semantics["subject"].capitalize())

    uml_classes.append(eclass)
    global leading_class_name
    leading_class_name = current_semantics["subject"].capitalize()

def process_relationship(doc, m):
    pass

# Start parsing
matcher = DependencyMatcher(nlp.vocab)

if sys.argv[1] == "class":
    matcher.add("copula class", [copula_class], on_match=on_match)
elif sys.argv[1] == "rel":
    matcher.add("REL", [], on_match=on_match)
matches = matcher(doc)

#print(matches)

print("# of matches: {matches}".format(matches=len(matches)))

pack = ecore.package_up(uml_classes, leading_class_name)
ecore.save_package(pack, out_path)