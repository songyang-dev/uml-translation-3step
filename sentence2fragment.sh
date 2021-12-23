#!/bin/bash

# Pipeline for transforming sentence to fragment
if [ $# -ne 3 ]; then
    echo "Usage: ./sentence2fragment.sh [class | rel] out_path_no_extension \"Your sentence.\""
    exit 1
fi

kind="$1"
out="$2"
sentence="$3"

echo "$sentence" | python parse.py "$kind" "$out".plantuml
# python ecore2plant.py "$out".ecore > "$out".plantuml
java -jar ~/Documents/Libs/JavaLib/plantuml.jar "$out".plantuml # make sure you have plantuml