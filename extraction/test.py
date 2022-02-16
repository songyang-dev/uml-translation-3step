"""
Run a test suite on the NLP extraction process
"""
from sys import argv, stderr
from typing import Callable

if len(argv) != 2:
    print("Usage: py test.py processed-csv", file=stderr)
    exit(1)

import os
import pandas as pd
import nlp_patterns
from utils import uml, inquire
import parse
import termcolor


# Initialize the test suite
CURRENT_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

TEMP_FOLDER = os.path.join(CURRENT_SCRIPT_DIR, "temp")
os.makedirs(TEMP_FOLDER, exist_ok=True)


# Read the preprocessed csv for classification
PREPROCESSED_CSV = os.path.join(os.getcwd(), argv[1])

FRAGMENTS = pd.read_csv(PREPROCESSED_CSV, header=0, index_col=0)

# Test one rule on the data set
def test_rule(
    kind: str,
    rule_name: str,
    rule_pattern: list[list[dict]],
    on_match: Callable[[dict], uml.UML],
):
    rule = nlp_patterns.BuiltUML("", kind)
    rule.add_rule(rule_name, rule_pattern, on_match)

    # stats
    passed = 0
    failed = 0

    passed_fragments = []
    passed_fragments_indices = []
    failed_fragments = []
    failed_fragments_indices = []

    # test the rule on every fragment of the same kind
    for index, fragment in FRAGMENTS.iterrows():

        if fragment["kind"] != kind:
            continue

        rule.clear_result()
        rule.set_sentence(fragment["english"])
        result = rule.parse(verbose=False)

        # matches
        if result != None:
            passed += 1
            passed_fragments.append(fragment["english"])
            passed_fragments_indices.append(index)

        # no match
        else:
            failed += 1
            failed_fragments.append(fragment["english"])
            failed_fragments_indices.append(index)

    # consider a semantic test to check for correctness

    print(
        f"{kind.capitalize()} rule: {rule_name}",
        termcolor.colored(f"Passed: {passed}", "green"),
        termcolor.colored(f"Failed: {failed}", "red"),
        sep="\t",
    )

    with open(
        os.path.join(TEMP_FOLDER, f"{kind}_{rule_name}_passed.csv"), "w"
    ) as pass_log:
        passed_details = pd.DataFrame(
            {"index": passed_fragments_indices, "fragment": passed_fragments}
        )
        passed_details.to_csv(pass_log)

    with open(
        os.path.join(TEMP_FOLDER, f"{kind}_{rule_name}_failed.csv"), "w"
    ) as fail_log:
        failed_details = pd.DataFrame(
            {"index": failed_fragments_indices, "fragment": failed_fragments}
        )
        failed_details.to_csv(fail_log)

    return passed_details, failed_details


def test_all_rules(kind: str):
    extractor = nlp_patterns.BuiltUML("", kind)

    if kind == "class":
        parse.add_class_rules(extractor)
    elif kind == "rel":
        parse.add_rel_rules(extractor)

    # stats
    passed = 0
    failed = 0

    passed_fragments = []
    passed_fragments_indices = []
    failed_fragments = []
    failed_fragments_indices = []

    # test the rule on every fragment of the same kind
    for index, fragment in FRAGMENTS.iterrows():

        if fragment["kind"] != kind:
            continue

        extractor.clear_result()
        extractor.set_sentence(fragment["english"])
        result = extractor.parse(verbose=False)

        # matches
        if result != None:
            passed += 1
            passed_fragments.append(fragment["english"])
            passed_fragments_indices.append(index)

        # no match
        else:
            failed += 1
            failed_fragments.append(fragment["english"])
            failed_fragments_indices.append(index)

        # consider a semantic test to check for correctness

    print(
        f"{kind.capitalize()} rule: ALL",
        termcolor.colored(f"Passed: {passed}", "green"),
        termcolor.colored(f"Failed: {failed}", "red"),
        sep="\t",
    )

    with open(os.path.join(TEMP_FOLDER, f"{kind}_ALL_passed.csv"), "w") as pass_log:
        passed_details = pd.DataFrame(
            {"index": passed_fragments_indices, "fragment": passed_fragments}
        )
        passed_details.to_csv(pass_log, index=False)

    with open(os.path.join(TEMP_FOLDER, f"{kind}_ALL_failed.csv"), "w") as fail_log:
        failed_details = pd.DataFrame(
            {"index": failed_fragments_indices, "fragment": failed_fragments}
        )
        failed_details.to_csv(fail_log, index=False)

    return passed_details, failed_details


def test_semantics():
    """
  Tests all the rules at once on the semantics of a fragment
  """
    extractor = nlp_patterns.BuiltUML("", "class")

    # stats
    passed = 0
    failed = 0
    wrong = 0

    passed_fragments = []
    passed_fragments_indices = []
    failed_fragments = []
    failed_fragments_indices = []
    wrong_fragments = []
    wrong_fragments_indices = []

    for index, fragment in FRAGMENTS.iterrows():
        kind = fragment["kind"]

        extractor.clear_rules()
        extractor.clear_result()

        if kind == "class":
            parse.add_class_rules(extractor)
        elif kind == "rel":
            parse.add_rel_rules(extractor)

        extractor.set_sentence(fragment["english"])
        result = extractor.parse(verbose=False)

        # matches
        if result != None:
            # check semantics
            ground_truth = inquire.get_uml_fragment(index)
            if ground_truth == result:
                passed += 1
                passed_fragments.append(fragment["english"])
                passed_fragments_indices.append(index)
            else:
                wrong += 1
                wrong_fragments.append(fragment["english"])
                wrong_fragments_indices.append(index)

        # no match
        else:
            failed += 1
            failed_fragments.append(fragment["english"])
            failed_fragments_indices.append(index)

    print(
        "Semantics",
        termcolor.colored(f"Passed: {passed}", "green"),
        termcolor.colored(f"Wrong: {wrong}", "yellow"),
        termcolor.colored(f"Failed: {failed}", "red"),
        sep="\t",
    )

    with open(os.path.join(TEMP_FOLDER, f"SEMANTICS_passed.csv"), "w") as pass_log:
        passed_details = pd.DataFrame(
            {"index": passed_fragments_indices, "fragment": passed_fragments}
        )
        passed_details.to_csv(pass_log, index=False)

    with open(os.path.join(TEMP_FOLDER, f"SEMANTICS_failed.csv"), "w") as wrong_log:
        failed_details = pd.DataFrame(
            {"index": failed_fragments_indices, "fragment": failed_fragments}
        )
        failed_details.to_csv(wrong_log, index=False)

    with open(os.path.join(TEMP_FOLDER, f"SEMANTICS_wrong.csv"), "w") as wrong_log:
        wrong_details = pd.DataFrame(
            {"index": wrong_fragments_indices, "fragment": wrong_fragments}
        )
        wrong_details.to_csv(wrong_log, index=False)

    return passed_details, failed_details, wrong_details


def unit_parsing(test_rule, test_all_rules):
    print(termcolor.colored("UNIT PARSING", "yellow"))
    print("OVERVIEW")
    test_rule(
        "class",
        "simple copula",
        [nlp_patterns.copula_class],
        nlp_patterns.process_copula_class,
    )
    test_rule(
        "class",
        "there is or exists",
        [nlp_patterns.expletive],
        nlp_patterns.process_expletive,
    )
    test_rule(
        "class", "compound", [nlp_patterns.compound], nlp_patterns.process_compound
    )
    test_rule(
        "class",
        "compound class explicit",
        [nlp_patterns.compound_class_explicit],
        nlp_patterns.process_compound_class_explicit,
    )
    test_rule(
        "class",
        "to have",
        [nlp_patterns.class_to_have],
        nlp_patterns.process_class_to_have,
    )
    test_rule(
        "class",
        "class named",
        [nlp_patterns.class_named],
        nlp_patterns.process_class_named,
    )
    test_rule(
        "class",
        "component of package",
        [nlp_patterns.component_package],
        nlp_patterns.process_component_package,
    )
    test_rule(
        "rel",
        "to have with multiplicity",
        [nlp_patterns.rel_to_have_multiplicity],
        nlp_patterns.process_rel_to_have_multiplicity,
    )
    test_rule(
        "rel",
        "passive voice",
        [nlp_patterns.passive_voice],
        nlp_patterns.process_passive_voice,
    )
    test_rule(
        "rel", "to have", [nlp_patterns.rel_to_have], nlp_patterns.process_rel_to_have
    )
    test_rule("rel", "composed", [nlp_patterns.composed], nlp_patterns.process_composed)
    test_rule(
        "rel",
        "active voice",
        [nlp_patterns.active_voice],
        nlp_patterns.process_active_voice,
    )
    test_rule(
        "rel",
        "active voice preposition",
        [nlp_patterns.active_voice_preposition],
        nlp_patterns.process_active_voice_preposition,
    )
    test_rule(
        "rel", "noun with", [nlp_patterns.noun_with], nlp_patterns.process_noun_with
    )
    print()
    print("DETAILS")
    print("Individual cases are logged at the temp folder next to this script")
    print()
    print(termcolor.colored("ALL RULES", "yellow"))
    test_all_rules("class")
    test_all_rules("rel")
    print()
    print("DETAILS")
    print("Individual cases are logged at the temp folder next to this script")
    print()


if __name__ == "__main__":
    unit_parsing(test_rule, test_all_rules)

    print(termcolor.colored("SEMANTIC EVALUATION", "yellow"))
    test_semantics()

