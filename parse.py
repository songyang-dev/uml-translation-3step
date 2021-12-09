# Parse the English text using rules

import sys
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
text = sys.stdin.read()


nlp = spacy.load("en_core_web_sm")
doc = nlp(text)


# Extract features for one class

# copula: The ... is ...
copula_pattern = [
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
        "RIGHT_ATTRS": {"DEP": {"IN": ["nsubj", "expl"]}}
    },
    # object of the verb
    {
        "LEFT_ID": "copula",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "attr"}
    }
]

matcher = DependencyMatcher(nlp.vocab)
matcher.add("CLASS", [copula_pattern])
matches = matcher(doc)

#print(matches)

print("# of matches: {matches}".format(matches=len(matches)))

# Abstract representation of a UML model
import ecore
from pyecore.ecore import EString

leading_class_name : str
uml_classes = []

# Process a copula match
def process_match(doc, copula_pattern, m):
    match_id, token_ids = m

    current_semantics = {}

    for i in range(len(token_ids)):
        matched_token = doc[token_ids[i]].text
        matched_rule = copula_pattern[i]["RIGHT_ID"]

        current_semantics[matched_rule] = matched_token

    eclass = ecore.declare_class(current_semantics["subject"].capitalize())
    ecore.attach_attribute(current_semantics["object"], of=eclass, etype=EString)

    uml_classes.append(eclass)
    global leading_class_name
    leading_class_name = current_semantics["subject"].capitalize()

for m in matches:
    # Each token_id corresponds to one pattern dict
    process_match(doc, copula_pattern, m)

pack = ecore.package_up(uml_classes, leading_class_name)
ecore.save_package(pack, out_path)