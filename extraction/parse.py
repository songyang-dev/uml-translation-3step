"""
Parse the English text using rules
"""
import os
import sys

if len(sys.argv) != 3:
    print(
        "Usage: py parse.py kind out_file [ < pipe text through stdin ]",
        file=sys.stderr,
    )
    exit(1)

if sys.argv[1] != "class" and sys.argv[1] != "rel":
    print("Acceptable kinds are: class | rel")
    exit(1)

# ------------------------------------------------------------------
# Start parsing
import nlp_patterns

out_path = sys.argv[2]

# Receives text to parse through stdin
# text = "The key has zero or more teeth."
text = sys.stdin.read()

if sys.argv[1] == "class":
    extractor = nlp_patterns.BuiltUML(text, "class")
    
    extractor.add_rule("simple copula", [nlp_patterns.copula_class], nlp_patterns.process_copula_class)
    extractor.add_rule("there is", [nlp_patterns.expletive], nlp_patterns.process_expletive)
    extractor.add_rule("compound", [nlp_patterns.compound], nlp_patterns.process_compound)

    PACKAGE = extractor.parse()

elif sys.argv[1] == "rel":
    extractor = nlp_patterns.BuiltUML(text, "rel")
    
    extractor.add_rule("to have multiplicity", [nlp_patterns.to_have_multiplicity], nlp_patterns.process_relationship_pattern)

    PACKAGE = extractor.parse()

else:
    raise Exception("Unknown fragment kind:{}".format(sys.argv[1]))

if PACKAGE is not None:
    path = os.path.abspath(os.path.dirname(__file__))
    PACKAGE.save(os.path.join(path, out_path))
else:
    print("No match actually", file=sys.stderr)
