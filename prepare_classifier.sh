#!/bin/bash

if [ $# -ne 2 ]; then
  echo "The script trains a classifier to determine the nature of an English fragment. The source directory is where fragments.csv and labels.csv are stored."
  echo "Usage: ./prepare_classifier.sh source-dir destination-dir"
  exit 1
fi

source_folder="$1"
destination_folder="$2"

# Prepares the classifier by preprocessing training data and training the best model
cd classification
python preprocess.py "../$source_folder" "../$destination_folder"
./train.sh ../`basename $destination_folder`/fragment_kinds.csv