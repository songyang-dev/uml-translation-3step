#!/bin/bash

# Trains the Bernoulli Naive Bayes classifier
if [ $# -ne 1 ]; then
  echo "Usage: ./train.sh csv-data-file"
  exit 1
fi

python classify.py "$1" bernoulliNB tfidf