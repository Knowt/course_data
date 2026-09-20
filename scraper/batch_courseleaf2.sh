#!/bin/bash
cd "$(dirname "$0")"
while read org url; do
  [ -z "$org" ] && continue
  echo "=== $org $url"; python3 courseleaf.py "$org" "$url" 2>&1 | grep -v "^FAILED" | tail -3
done <<'LIST'
yale.edu https://catalog.yale.edu/
brown.edu https://bulletin.brown.edu/
nd.edu https://catalog.nd.edu/
wustl.edu https://bulletin.wustl.edu/
georgetown.edu https://bulletin.georgetown.edu/
tulane.edu https://catalog.tulane.edu/
iu.edu https://catalog.iu.edu/
montclair.edu http://catalog.montclair.edu/
rice.edu https://ga.rice.edu/
msstate.edu https://catalog.msstate.edu/
csudh.edu https://catalog.csudh.edu/
LIST
echo "=== COURSELEAF BATCH DONE"
