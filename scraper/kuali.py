"""Kuali catalogs: <school>.kuali.co JSON API.

usage: python3 kuali.py <org> <tenant base url, e.g. https://unm.kuali.co>
"""
import re
import sys

from common import get_json, write_csv


def main(org, base):
    catalogs = get_json(f"{base}/api/v1/catalog/public/catalogs") or []
    latest_year = max(c.get("startDate", "")[:4] for c in catalogs)
    candidates = [c for c in catalogs if c.get("startDate", "").startswith(latest_year)]
    by_size = [(get_json(f"{base}/api/v1/catalog/courses/{c['_id']}") or [], c) for c in candidates]
    courses, catalog = max(by_size, key=lambda pair: len(pair[0]))
    print(f"{org}: using catalog {catalog.get('title')} ({catalog['_id']}), {len(courses)} courses", file=sys.stderr)
    rows = []
    for c in courses:
        raw = c.get("__catalogCourseId") or ""
        code = re.sub(r"^([A-Z&]+)(\d)", r"\1 \2", raw)
        subject = (c.get("subjectCode") or {}).get("description") or ""
        rows.append([code, c.get("title") or "", "", subject, "", ""])
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
