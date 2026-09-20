"""Northern Arizona University catalog (catalog.nau.edu/Courses/results). No subject list is exposed, but a
keyword search matches titles and descriptions, so a few single-letter keywords cover the whole catalog.

usage: python3 nau.py nau.edu [term ...]   (default 1267 = Fall 2026, 1261 = Spring 2026)
"""
import html
import re
import sys

from common import clean, get, write_csv

URL = "https://catalog.nau.edu/Courses/results?term={term}&keyword={keyword}"
ITEM = re.compile(r'<dt[^>]*\bsubject="([A-Z]+)"[^>]*\bcatnum="(\d+[A-Z]?)"[^>]*class="result-item"[^>]*>.*?<a[^>]*>\s*[A-Z]+\s+\S+\s*-\s*(.*?)\s*</a>', re.S)
KEYWORDS = ["a", "e", "i", "o", "u", "y"]


def main(org, *terms):
    rows = []
    for term in terms or ("1267", "1261"):
        for keyword in KEYWORDS:
            page = get(URL.format(term=term, keyword=keyword), timeout=180)
            found = ITEM.findall(page)
            print(f"  {org}: term {term} keyword '{keyword}' -> {len(found)}", file=sys.stderr)
            for subject, number, title in found:
                rows.append([f"{subject} {number}", clean(html.unescape(title)), "", subject, "", ""])
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
