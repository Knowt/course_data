#!/bin/bash
cd "$(dirname "$0")"
export NODE_PATH=/Users/abhi/Documents/Knowt.nosync/Goliath/node_modules
while read org url; do
  [ -z "$org" ] && continue
  echo "=== $org $url"; python3 acalog.py "$org" "$url" 2>&1 | grep -vE "page [0-9]+, [0-9]+ new" | tail -3
done <<'LIST'
ohio.edu https://catalogs.ohio.edu/
unr.edu https://catalog.unr.edu/
mtsu.edu https://catalog.mtsu.edu/
rowan.edu https://catalog.rowan.edu/
charlotte.edu https://catalog.charlotte.edu/
csueastbay.edu https://catalog.csueastbay.edu/
csusm.edu https://catalog.csusm.edu/
hccs.edu https://catalog.hccs.edu/
LIST
echo "=== ACALOG BATCH DONE"
