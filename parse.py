# Parse the English text using rules

import sys
if len(sys.argv) != 2:
    print(
        "Usage: py parse.py kind [ < pipe text through stdin ]", file=sys.stderr)
    exit(1)

if sys.argv[1] != "class" and sys.argv[1] != "rel":
    print("Acceptable kinds are: class | rel")
    exit(1)

from spacy.matcher import DependencyMatcher
import spacy


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

for m in matches:
    print("")
    # Each token_id corresponds to one pattern dict
    match_id, token_ids = m
    for i in range(len(token_ids)):
        matched_token = doc[token_ids[i]].text
        matched_rule = copula_pattern[i]["RIGHT_ID"]
        print(matched_rule + ":", matched_token)
