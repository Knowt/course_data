#!/bin/bash
cd "$(dirname "$0")"
while read org host; do
  [ -z "$org" ] && continue
  echo "=== $org $host"; python3 coursedog.py "$org" "$host" 2>&1 | grep -v "/" | tail -2
done <<'LIST'
fau.edu catalog.fau.edu
stanford.edu bulletin.stanford.edu
emory.edu catalog.emory.edu
tccd.edu catalog.tccd.edu
maricopa.edu catalog.maricopa.edu
_cuny_hunter_ug hunter-undergraduate.catalog.cuny.edu
_cuny_hunter_gr hunter-graduate.catalog.cuny.edu
_cuny_baruch_ug baruch-undergraduate.catalog.cuny.edu
_cuny_baruch_gr baruch-graduate.catalog.cuny.edu
_cuny_ccny_ug ccny-undergraduate.catalog.cuny.edu
_cuny_ccny_gr ccny-graduate.catalog.cuny.edu
_cuny_qc_ug qc-undergraduate.catalog.cuny.edu
_cuny_qc_gr qc-graduate.catalog.cuny.edu
LIST
python3 - <<'PY'
import csv, glob, os
from common import write_csv, OUT_DIR
names = {"hunter": "Hunter College", "baruch": "Baruch College", "ccny": "City College", "qc": "Queens College"}
rows = []
for f in sorted(glob.glob(os.path.join(OUT_DIR, "_cuny_*.csv"))):
    college = names[os.path.basename(f).split("_")[2]]
    for r in csv.DictReader(open(f)):
        rows.append([r["courseId"], r["courseName"], r["courseCredits"], r["courseSubject"], r["courseLevel"], college])
    os.remove(f)
write_csv("cuny.edu", rows)
PY
echo "=== COURSEDOG BATCH DONE"
