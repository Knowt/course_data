"""Austin Community College: course descriptions live on a legacy CMS (www6.austincc.edu/cms/site/www/catalog/catalog.php),
one page per rubric, linked from catalog.austincc.edu/course-descriptions/current-courses/.

usage: python3 austincc.py austincc.edu
"""
import concurrent.futures as cf
import html
import re
import sys

from common import clean, get, write_csv

INDEX = "https://catalog.austincc.edu/course-descriptions/current-courses/"
TITLE = re.compile(r"class='crsTitle'[^>]*>\s*<A NAME='[^']*'>\s*([A-Z]{2,5})\s?(\d{4}[A-Z]?)\s*-\s*(.*?)\s*(?:\((\d+)-\d+-\d+\))?\s*(?:</a>)?\s*</th>", re.S | re.I)


def main(org):
    index = get(INDEX)
    urls = sorted({html.unescape(u) for u in re.findall(r'href="(https://www6\.austincc\.edu/cms/site/www/catalog/catalog\.php[^"]+)"', index)})
    print(f"{org}: {len(urls)} rubric pages", file=sys.stderr)
    rows = []
    with cf.ThreadPoolExecutor(8) as ex:
        for page in ex.map(get, urls):
            for subject, number, title, credits in TITLE.findall(page):
                rows.append([f"{subject} {number}", clean(html.unescape(title)), credits, subject, "", ""])
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
