#!/bin/bash

plantuml=~/Documents/My\ Documents/Scripts/Libs/plantuml/plantuml-1.2021.16.jar # where your plantuml.jar is

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
java -jar "$plantuml" "$out".plantuml # make sure you have plantuml