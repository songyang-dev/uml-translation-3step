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

# # Initialize the test suite
# CURRENT_SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

# TEMP_FOLDER = os.path.join(CURRENT_SCRIPT_DIR,"temp")
# os.makedirs(TEMP_FOLDER, exist_ok=True)


# Read the preprocessed csv for classification
PREPROCESSED_CSV = os.path.join(os.getcwd(), argv[1])

FRAGMENTS = pd.read_csv(PREPROCESSED_CSV, header=0, index_col=0)

def test_rule(kind: str, rule_name: str, rule_pattern: list[list[dict]], on_match: Callable[[dict], uml.UML]):
  rule = nlp_patterns.BuiltUML("")
  rule.add_rule(rule_name, rule_pattern, on_match)

  for fragment, fragment_kind in zip(FRAGMENTS.english, FRAGMENTS.kind):
    
    if fragment_kind != kind:
      continue

    rule.set_sentence(fragment)
    rule.parse()

    # no matches
    if rule.uml_result == None:
      print("no match")

    # a match
    else:
      print("matched!")

if __name__ == "__main__":
  test_rule("class", "simple copula", [nlp_patterns.copula_class], nlp_patterns.process_copula_class)