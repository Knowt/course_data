#!/bin/bash
cd "$(dirname "$0")"
export NODE_PATH=/Users/abhi/Documents/Knowt.nosync/Goliath/node_modules
while read org url; do
  [ -z "$org" ] && continue
  echo "=== $org $url"; python3 courseleaf.py "$org" "$url" 2>&1 | grep -v "^FAILED" | tail -3
done <<'LIST'
brown.edu https://bulletin.brown.edu/
nd.edu https://catalog.nd.edu/
georgetown.edu https://bulletin.georgetown.edu/
tulane.edu https://catalog.tulane.edu/
wustl.edu https://bulletin.wustl.edu/
rice.edu https://ga.rice.edu/
iu.edu https://catalog.iu.edu/
csudh.edu https://catalog.csudh.edu/
msstate.edu https://catalog.msstate.edu/
montclair.edu http://catalog.montclair.edu/
LIST
echo "=== COURSELEAF BATCH DONE"
