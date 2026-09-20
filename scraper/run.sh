#!/bin/bash
# usage: ./run.sh <org>   — replays the scrape recorded for that org in sources.csv
cd "$(dirname "$0")"
export NODE_PATH=${NODE_PATH:-../../Goliath/node_modules}
line=$(grep "^$1," sources.csv) || { echo "no entry for $1 in sources.csv"; exit 1; }
script=$(echo "$line" | cut -d, -f2)
args=$(echo "$line" | cut -d, -f3- | sed 's/^"//; s/"$//; s/ (.*//')
[ -z "$script" ] && { echo "$1 has no recorded script"; exit 1; }
if [ "$script" = "coursedog.py" ] && [ "$1" = "cuny.edu" ]; then echo "cuny.edu: run coursedog.py once per host listed in sources.csv, then merge"; exit 1; fi
python3 "$script" "$1" $args
