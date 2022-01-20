"""
Run a test suite on the NLP extraction process
"""
from sys import argv, stderr
from typing import Callable

if len(argv) != 2:
  print("Usage: py run.py processed-csv", file=stderr)
  exit(1)

import os
import pandas as pd
import nlp_patterns
from utils import uml
import termcolor


# Initialize the test suite
CURRENT_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

TEMP_FOLDER = os.path.join(CURRENT_SCRIPT_DIR,"temp")
os.makedirs(TEMP_FOLDER, exist_ok=True)


# Read the preprocessed csv for classification
PREPROCESSED_CSV = os.path.join(os.getcwd(), argv[1])

FRAGMENTS = pd.read_csv(PREPROCESSED_CSV, header=0, index_col=0)

def test_rule(kind: str, rule_name: str, rule_pattern: list[list[dict]], on_match: Callable[[dict], uml.UML]):
  rule = nlp_patterns.BuiltUML("")
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
    rule.parse(verbose=False)

    # matches
    if rule.uml_result != None:
      passed += 1
      passed_fragments.append(fragment["english"])
      passed_fragments_indices.append(index)

    # no match
    else:
      failed += 1
      failed_fragments.append(fragment["english"])
      failed_fragments_indices.append(index)

  # consider a semantic test to check for correctness

  print(f"Rule: {rule_name}", termcolor.colored(f"Passed: {passed}", 'green'), termcolor.colored(f"Failed: {failed}", 'red'))

  with open(os.path.join(TEMP_FOLDER, f"{kind}_{rule_name}_passed.csv"), "w") as pass_log:
    pd.DataFrame({"index": passed_fragments_indices, "fragment": passed_fragments}).to_csv(pass_log)

  with open(os.path.join(TEMP_FOLDER, f"{kind}_{rule_name}_failed.csv"), "w") as fail_log:
    pd.DataFrame({"index": failed_fragments_indices, "fragment": failed_fragments}).to_csv(fail_log)



if __name__ == "__main__":
  test_rule("class", "simple copula", [nlp_patterns.copula_class], nlp_patterns.process_copula_class)