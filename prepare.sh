#!/bin/bash

# Preprocess the data for further use
./prepare_classifier.sh .. data/
python prepare_test.py ..
python extraction/preprocess.py data/fragment_kinds.csv data/split.csv