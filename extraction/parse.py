"""
Parse the English text using rules
"""
from . import nlp_patterns

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


class LazyLoadedExtractor:
    """
    See ../translate.py for example usage
    """

    def __init__(self, text: str, kind: str) -> None:
        self.extractor = nlp_patterns.BuiltUML(sentence=text, kind=kind)

    def handle_class(self, verbose=False):
        extractor = self.extractor

        add_class_rules(extractor)

        PACKAGE = extractor.parse(verbose=verbose)

        # integrity check
        if PACKAGE is not None and len(PACKAGE.classes) != 1:
            raise Exception(
                "Class fragment has more than one class: {}".format(
                    PACKAGE.package_name
                )
            )

        return PACKAGE

    def handle_rel(self, verbose=False):
        extractor = self.extractor

        add_rel_rules(extractor)

        PACKAGE = extractor.parse(verbose=verbose)

        # integrity check
        if PACKAGE is not None and len(PACKAGE.classes) != 2:
            raise Exception(
                "Rel fragment does not have exactly two classes: {}".format(
                    PACKAGE.package_name
                )
            )

        return PACKAGE


def add_class_rules(extractor: nlp_patterns.BuiltUML):
    extractor.add_rule(
        "simple copula", [nlp_patterns.copula_class], nlp_patterns.process_copula_class
    )
    extractor.add_rule(
        "there is or exists", [nlp_patterns.expletive], nlp_patterns.process_expletive
    )
    extractor.add_rule(
        "compound", [nlp_patterns.compound], nlp_patterns.process_compound
    )
    extractor.add_rule(
        "compound class explicit",
        [nlp_patterns.compound_class_explicit],
        nlp_patterns.process_compound_class_explicit,
    )
    extractor.add_rule(
        "to have", [nlp_patterns.class_to_have], nlp_patterns.process_class_to_have
    )
    extractor.add_rule(
        "class named", [nlp_patterns.class_named], nlp_patterns.process_class_named
    )
    extractor.add_rule(
        "component of package",
        [nlp_patterns.component_package],
        nlp_patterns.process_component_package,
    )
    extractor.add_rule(
        "3 component and clause",
        [nlp_patterns.class_to_have_and_many_clauses],
        nlp_patterns.process_class_to_have_and_many_clauses,
    )
    extractor.add_rule(
        "2 component and clause",
        [nlp_patterns.class_to_have_and_clause],
        nlp_patterns.process_class_to_have_and_clause,
    )


def add_rel_rules(extractor: nlp_patterns.BuiltUML):
    extractor.add_rule(
        "to have multiplicity",
        [nlp_patterns.rel_to_have_multiplicity],
        nlp_patterns.process_rel_to_have_multiplicity,
    )
    extractor.add_rule(
        "passive voice",
        [nlp_patterns.passive_voice],
        nlp_patterns.process_passive_voice,
    )
    extractor.add_rule(
        "to have", [nlp_patterns.rel_to_have], nlp_patterns.process_rel_to_have
    )
    extractor.add_rule(
        "composed", [nlp_patterns.composed], nlp_patterns.process_composed
    )
    extractor.add_rule(
        "active voice", [nlp_patterns.active_voice], nlp_patterns.process_active_voice
    )
    extractor.add_rule(
        "active voice preposition",
        [nlp_patterns.active_voice_preposition],
        nlp_patterns.process_active_voice_preposition,
    )
    extractor.add_rule(
        "noun with", [nlp_patterns.noun_with], nlp_patterns.process_noun_with
    )
    extractor.add_rule(
        "copula rel", [nlp_patterns.copula_rel], nlp_patterns.process_copula_rel
    )


if __name__ == "__main__":

    if sys.argv[1] == "class":
        extractor = LazyLoadedExtractor(text, "class")
        PACKAGE = extractor.handle_class(verbose=True)

    elif sys.argv[1] == "rel":
        extractor = LazyLoadedExtractor(text, "rel")
        PACKAGE = extractor.handle_rel(verbose=True)

    else:
        raise Exception("Unknown fragment kind:{}".format(sys.argv[1]))

    if PACKAGE is not None:
        path = os.path.abspath(os.path.dirname(__file__))
        PACKAGE.save(os.path.join(path, out_path))
    else:
        print("No match actually", file=sys.stderr)
