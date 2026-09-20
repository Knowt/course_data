"""Princeton: registrar course-offerings API (public bearer token from registrar.princeton.edu), unioned over terms.

usage: python3 princeton.py princeton.edu [term ...]   (term codes like 1272 = 1 + YY + 2 fall / 4 spring)
"""
import sys

from common import get_json, write_csv

API = "https://api.princeton.edu/registrar/course-offerings/1.0.7/classes/{term}"
HEADERS = {
    "accept": "application/json",
    "authorization": "Bearer Njk5ZDU5YWUtYzIwMS0zMmY2LWI3OTItMzIxYjQ4NDdkNTQxOnJlZ2lzdHJhcmFwaUBjYXJib24uc3VwZXI=",
    "origin": "https://registrar.princeton.edu",
    "referer": "https://registrar.princeton.edu/",
    "Accept-Encoding": "identity",
}
CAREER = {"UGRD": "Undergraduate", "GRAD": "Graduate"}


def main(org, *terms):
    rows = []
    for term in terms or ("1252", "1254", "1262", "1264", "1272"):
        classes = ((get_json(API.format(term=term), HEADERS) or {}).get("classes") or {}).get("class") or []
        print(f"{org}: term {term}, {len(classes)} sections", file=sys.stderr)
        for c in classes:
            rows.append([
                f"{c['subject']} {c['catnum'].strip()}",
                c.get("long_title") or "",
                "",
                c["subject"],
                CAREER.get(c.get("acad_career"), c.get("acad_career") or ""),
                "",
            ])
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
