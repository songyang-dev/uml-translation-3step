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
# text = "The key to a good life is music."
text = sys.stdin.read()


nlp = spacy.load("en_core_web_sm")
doc = nlp(text)

# ------------------------------------------------------------
# Extract features for one class

# copula: The ... is ...
copula_class = [
    # Pattern is: "The (subject) is a class ..."
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
relationship_pattern = [
    # Pattern is: A (noun for class A) has (numerical multiplicity) (noun for class B)
    # Extracted info: Class A has a relationship of a certain multiplicity with Class B
    {
        "RIGHT_ID": "verb",
        "RIGHT_ATTRS": {"LEMMA": "have"}
    },
    {
        "LEFT_ID": "verb",
        "REL_OP": ">",
        "RIGHT_ID": "subject",
        "RIGHT_ATTRS": {"DEP": "nsubj"}
    },
    {
        "LEFT_ID": "verb",
        "REL_OP": ">",
        "RIGHT_ID": "object",
        "RIGHT_ATTRS": {"DEP": "dobj"}
    },
    {
        "LEFT_ID": "object",
        "REL_OP": ">",
        "RIGHT_ID": "number",
        "RIGHT_ATTRS": {"POS": "NUM"}
    }
]

# Multiplicity pattern
multiplicity_terms = ["0 or several", "one and only one", "one or more", "zero or more", "zero or one", "at least one"]
multiplicity_pattern = [nlp.make_doc(text) for text in multiplicity_terms]

# Abstract representation of a UML model
import uml

leading_class_name = ""
uml_classes = []

def on_match(matcher, doc, i, matches):

    match_id, _ = matches[i]
    string_id = nlp.vocab.strings[match_id]

    if string_id == "copula class":
        process_copula_class(doc, matches[i])

    elif string_id == "REL":
        process_relationship(doc, matches[i])

    elif string_id == "multiplicity":
        process_multiplicity(doc, matches[i])

# Process a copula match
def process_copula_class(doc, m):
    _, token_ids = m

    current_semantics = {}

    for i in range(len(token_ids)):
        matched_token = doc[token_ids[i]].text
        matched_rule = copula_class[i]["RIGHT_ID"]

        current_semantics[matched_rule] = matched_token

    eclass = uml.UMLClass(current_semantics["subject"].capitalize(), "class")

    uml_classes.append(eclass)
    global leading_class_name
    leading_class_name = current_semantics["subject"].capitalize()

def process_relationship(doc, m):
    pass

def process_multiplicity(doc, m):
    pass


# ------------------------------------------------------------------
# Start parsing
matcher = DependencyMatcher(nlp.vocab)

if sys.argv[1] == "class":
    matcher.add("copula class", [copula_class], on_match=on_match)
elif sys.argv[1] == "rel":
    matcher.add("REL", [], on_match=on_match)
    matcher.add("multiplicity", [multiplicity_pattern], on_match=on_match)
matches = matcher(doc)

#print(matches)

print("# of matches: {matches}".format(matches=len(matches)))

pack = uml.UML(leading_class_name)
pack.classes = uml_classes
pack.save(out_path)
