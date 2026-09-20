"""ASU: catalog.apps.asu.edu class search API, unioned over the given terms (default Spring + Fall 2026).

usage: python3 asu.py asu.edu [term ...]
"""
import concurrent.futures as cf
import sys

from common import get_json, write_csv

API = "https://eadvs-cscc-catalog-api.apps.asu.edu/catalog-microservices/api/v1/search"
HEADERS = {"Authorization": "Bearer null", "Origin": "https://catalog.apps.asu.edu", "Referer": "https://catalog.apps.asu.edu/", "Accept-Encoding": "identity"}
CAREER = {"UGRD": "Undergraduate", "GRAD": "Graduate", "LAW": "Law"}


def classes(subject, term):
    url = f"{API}/classes?refine=Y&campusOrOnlineSelection=A&catalogNbr=&promod=F&searchType=all&subject={subject}&term={term}"
    return (get_json(url, HEADERS) or {}).get("classes", [])


def main(org, *terms):
    terms = terms or ("2261", "2267")
    groups = get_json(f"{API}/subjects", HEADERS) or {}
    subjects = sorted({s["SUBJECT"] for group in groups.values() for s in group})
    print(f"{org}: {len(subjects)} subjects x {len(terms)} terms", file=sys.stderr)
    jobs = [(s, t) for s in subjects for t in terms]
    rows = []
    with cf.ThreadPoolExecutor(8) as ex:
        for (subject, term), found in zip(jobs, ex.map(lambda j: classes(*j), jobs)):
            for c in found:
                k = c["CLAS"]
                lo, hi = (k.get("UNITSMINIMUM") or "").strip(), (k.get("UNITSMAXIMUM") or "").strip()
                rows.append([
                    f"{k['SUBJECT']} {k['CATALOGNBR']}",
                    k.get("COURSETITLELONG") or k.get("TITLE") or "",
                    lo if lo == hi or not hi else f"{lo}-{hi}",
                    k.get("SUBJECTDESCRIPTION") or "",
                    CAREER.get(k.get("ACADCAREER"), k.get("ACADCAREER") or ""),
                    "",
                ])
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
