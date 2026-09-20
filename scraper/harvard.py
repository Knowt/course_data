"""Harvard: my.harvard.edu public course search (JSON envelope around HTML course cards, 15 per page).

usage: python3 harvard.py harvard.edu
"""
import concurrent.futures as cf
import html
import json
import re
import sys

from common import clean, get, write_csv

CHUNK = 60
URL ="https://my.harvard.edu/search/?q=&school=All&term=All&sort=relevance&browseSchool=false&page={page}"
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
    print(f"{org}: {page(1).get('total_hits')} hits", file=sys.stderr)
    rows, seen, start = [], set(), 1
    with cf.ThreadPoolExecutor(6) as ex:
        while start < 3000:
            new = 0
            for data in ex.map(page, range(start, start + CHUNK)):
                for card in (data.get("hits") or "").split("<!-- Course Card -->")[1:]:
                    course_id = re.search(r'data-course-id="(\d+)"', card)
                    if not course_id or course_id.group(1) in seen:
                        continue
                    seen.add(course_id.group(1))
                    parsed = parse(card)
                    if parsed:
                        rows.append(parsed)
                        new += 1
            print(f"  {org}: pages {start}-{start + CHUNK - 1}, {new} new, {len(rows)} total", file=sys.stderr)
            if new == 0:
                break
            start += CHUNK
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
