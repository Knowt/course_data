"""Coursedog catalogs: app.coursedog.com public search API behind catalog.<school>.edu SPAs.

usage: python3 coursedog.py <org> <catalog host, e.g. bulletin.fsu.edu>
"""
import json
import sys

from common import get_json, write_csv

API = "https://app.coursedog.com/api/v1"
COLUMNS = "code,subjectCode,courseNumber,name,longName,credits,career,status,departments"


def main(org, host):
    site = get_json(f"{API}/catalogs/urls?url={host}")
    school, catalog = site["school"], site["catalog"]
    print(f"{org}: school {school}, catalog {catalog.get('displayName')} ({catalog['id']})", file=sys.stderr)
    headers = {"Content-Type": "application/json", "Origin": f"https://{host}", "Referer": f"https://{host}/"}
    body = json.dumps(catalog.get("coursesFilters") or {"condition": "and", "filters": []}).encode()
    rows, skip, total = [], 0, None
    while total is None or skip < total:
        url = f"{API}/cm/{school}/courses/search/%24filters?catalogId={catalog['id']}&skip={skip}&limit=1000&columns={COLUMNS}&formatDependents=false"
        page = get_json(url, headers, body)
        if not page:
            break
        total = page.get("listLength", 0)
        for c in page.get("data", []):
            subject_code, number = c.get("subjectCode") or "", c.get("courseNumber") or ""
            code = f"{subject_code} {number}".strip() if subject_code and number else c.get("code") or ""
            hours = (c.get("credits") or {}).get("creditHours") or {}
            lo, hi = hours.get("min"), hours.get("max")
            cred = "" if lo is None else (str(lo) if lo == hi or hi is None else f"{lo}-{hi}")
            depts = c.get("departments") or []
            subject = depts[0].get("displayName", "") if depts and isinstance(depts[0], dict) else ""
            rows.append([code, c.get("longName") or c.get("name") or "", cred, subject, c.get("career") or "", ""])
        skip += 1000
        print(f"  {org}: {min(skip, total)}/{total}", file=sys.stderr)
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
