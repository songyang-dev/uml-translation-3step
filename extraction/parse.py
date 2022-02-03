"""
Parse the English text using rules
"""
import nlp_patterns

if __name__ == "__main__":
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

    out_path = sys.argv[2]

    # Receives text to parse through stdin
    # text = "A class named Job."
    text = sys.stdin.read()

def handle_class(text, verbose=True):
    extractor = nlp_patterns.BuiltUML(text, "class")
    
    add_class_rules(extractor)

    PACKAGE = extractor.parse(verbose=verbose)
    return PACKAGE

def add_class_rules(extractor: nlp_patterns.BuiltUML):
    extractor.add_rule("simple copula", [nlp_patterns.copula_class], nlp_patterns.process_copula_class)
    extractor.add_rule("there is or exists", [nlp_patterns.expletive], nlp_patterns.process_expletive)
    extractor.add_rule("compound", [nlp_patterns.compound], nlp_patterns.process_compound)
    extractor.add_rule("compound class explicit", [nlp_patterns.compound_class_explicit], nlp_patterns.process_compound_class_explicit)
    extractor.add_rule("to have", [nlp_patterns.class_to_have], nlp_patterns.process_class_to_have)
    extractor.add_rule("class named", [nlp_patterns.class_named], nlp_patterns.process_class_named)
    extractor.add_rule("component of package", [nlp_patterns.component_package], nlp_patterns.process_component_package)

def handle_rel(text, verbose=True):
    extractor = nlp_patterns.BuiltUML(text, "rel")
    
    add_rel_rules(extractor)

    PACKAGE = extractor.parse(verbose=verbose)
    return PACKAGE

def add_rel_rules(extractor: nlp_patterns.BuiltUML):
    extractor.add_rule("to have multiplicity", [nlp_patterns.rel_to_have_multiplicity], nlp_patterns.process_rel_to_have_multiplicity)
    extractor.add_rule("passive voice", [nlp_patterns.passive_voice], nlp_patterns.process_passive_voice)

if __name__ == "__main__":

    if sys.argv[1] == "class":
        PACKAGE = handle_class(text)

    elif sys.argv[1] == "rel":
        PACKAGE = handle_rel(text)

    else:
        raise Exception("Unknown fragment kind:{}".format(sys.argv[1]))

    if PACKAGE is not None:
        path = os.path.abspath(os.path.dirname(__file__))
        PACKAGE.save(os.path.join(path, out_path))
    else:
        print("No match actually", file=sys.stderr)
