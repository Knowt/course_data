#!/bin/bash
cd "$(dirname "$0")"
while read org url; do
  [ -z "$org" ] && continue
  echo "=== $org $url"; python3 courseleaf.py "$org" "$url" 2>&1 | grep -v "^FAILED" | tail -3
done <<'LIST'
northwestern.edu https://catalogs.northwestern.edu/
utep.edu https://catalog.utep.edu/
shsu.edu https://catalog.shsu.edu/
towson.edu https://catalog.towson.edu/
uab.edu https://catalog.uab.edu/
odu.edu https://catalog.odu.edu/
uncg.edu https://catalog.uncg.edu/
msstate.edu https://catalog.msstate.edu/
csudh.edu https://catalog.csudh.edu/
yale.edu https://catalog.yale.edu/
brown.edu https://bulletin.brown.edu/
nd.edu https://catalog.nd.edu/
wustl.edu https://bulletin.wustl.edu/
georgetown.edu https://bulletin.georgetown.edu/
tulane.edu https://catalog.tulane.edu/
iu.edu https://catalog.iu.edu/
montclair.edu http://catalog.montclair.edu/
rice.edu https://ga.rice.edu/
LIST
echo "=== COURSELEAF BATCH DONE"
