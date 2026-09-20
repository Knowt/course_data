"""Harvard: my.harvard.edu public course search (JSON envelope around HTML course cards, 15 per page).

usage: python3 harvard.py harvard.edu
"""
import concurrent.futures as cf
import html
import json
import math
import re
import sys

from common import clean, get, write_csv

URL = "https://my.harvard.edu/search/?q=&school=All&term=All&sort=relevance&browseSchool=false&page={page}"
HEADERS = {"accept": "*/*", "referer": "https://my.harvard.edu/", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin"}
CODE = re.compile(r'badge badge-light[^>]*>\s*([A-Z&-]+\s+[0-9A-Z.-]+)\s*<')
TITLE = re.compile(r'<h2[^>]*>\s*<a[^>]*href="/course/[^"]*"[^>]*>\s*(.*?)\s*</a>', re.S)
SCHOOL = re.compile(r'href="/school/([^"]+)"')
STRIP = re.compile(r"<[^>]+>")


def page(n):
    body = get(URL.format(page=n), HEADERS)
    return json.loads(body) if body else {}


def parse(card):
    code, title, school = CODE.search(card), TITLE.search(card), SCHOOL.search(card)
    if not (code and title):
        return None
    school = school.group(1) if school else ""
    segments = [s for s in (clean(html.unescape(x)) for x in STRIP.sub("|", card).split("|")) if s and s != "·"]
    dept = ""
    if school in segments:
        after = segments[segments.index(school) + 1 :]
        dept = after[0] if after and len(after[0]) < 60 else ""
    return [re.sub(r"\s+", " ", code.group(1)), clean(html.unescape(title.group(1))), "", dept, school, ""]


def main(org):
    first = page(1)
    total = int(first.get("total_hits", 0))
    pages = math.ceil(total / 15)
    print(f"{org}: {total} hits, {pages} pages", file=sys.stderr)
    rows = []
    with cf.ThreadPoolExecutor(6) as ex:
        for n, data in enumerate(ex.map(page, range(1, pages + 1)), start=1):
            for card in (data.get("hits") or "").split("<!-- Course Card -->")[1:]:
                parsed = parse(card)
                if parsed:
                    rows.append(parsed)
            if n % 100 == 0:
                print(f"  {org}: page {n}/{pages}, {len(rows)} rows", file=sys.stderr)
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
