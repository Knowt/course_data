"""CourseLeaf FOSE course search (courses.yale.edu, cab.brown.edu, ...): POST /api/?page=fose&route=search per term.

usage: python3 fose.py <org> <host> <srcdb> [srcdb ...]   (find srcdb term codes in the site's term dropdown)
"""
import json
import sys
import urllib.parse

from common import get_json, write_csv

UNDERGRAD_COLLEGES = {"YC", "UG"}


def search(host, srcdb):
    body = urllib.parse.quote(json.dumps({"other": {"srcdb": srcdb}, "criteria": [{"field": "stat", "value": "A,F"}]}))
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "origin": f"https://{host}",
        "referer": f"https://{host}/",
        "x-requested-with": "XMLHttpRequest",
    }
    return (get_json(f"https://{host}/api/?page=fose&route=search&stat=A%2CF", headers, body.encode()) or {}).get("results", [])


def main(org, host, *srcdbs):
    rows = []
    for srcdb in srcdbs:
        results = search(host, srcdb)
        print(f"{org}: {srcdb} -> {len(results)} sections", file=sys.stderr)
        for r in results:
            code = r.get("code") or ""
            level = "Undergraduate" if r.get("col") in UNDERGRAD_COLLEGES else ""
            rows.append([code, r.get("title") or "", "", code.split(" ")[0], level, ""])
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
