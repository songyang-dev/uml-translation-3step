#!/bin/bash

# Trains the classifier
if [ $# -ne 1 ]; then
  echo "Usage: ./train.sh csv-data-file"
  exit 1
fi

python classify.py "$1"