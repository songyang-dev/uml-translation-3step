#!/bin/bash

# Parses a fragment quickly. Results are located in out.plantuml
if [ $# -ne 2 ]; then
  echo "The script trains a classifier to determine the nature of an English fragment. The source directory is where fragments.csv and labels.csv are stored."
  echo "Usage: ./quick_parse.sh kind fragment-text"
  exit 1
fi

echo "$2" | python -m extraction.parse $1 ../out.plantuml