#!/bin/bash

if [ ! -f "$1" ]
then
    printf "You must supply a valid text file with series ids in the first column.\n"
    exit 1
fi

scriptPath="${0%/*}"
melimanPath="$scriptPath/../meliman.py"

awk '// { print $1; }' "$1" | xargs -n1 "$melimanPath" -w
