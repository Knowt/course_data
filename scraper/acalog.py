"""Acalog / Modern Campus catalogs: content.php?catoid=X&navoid=Y course listings behind an AWS WAF JS challenge.

usage: NODE_PATH=<goliath>/node_modules python3 acalog.py <org> <catalog index url> [more index urls, e.g. one per catoid]
"""
import html
import json
import os
import re
import subprocess
import sys
from collections import Counter
from urllib.parse import urljoin

from common import clean, get, write_csv

HERE = os.path.dirname(os.path.abspath(__file__))
COURSE = re.compile(r'preview_course_nopop\.php\?catoid=(\d+)&(?:amp;)?coid=(\d+)"[^>]*>(.*?)</a>', re.S)
NAV = re.compile(r'<a[^>]*href="([^"]*content\.php\?catoid=(\d+)&(?:amp;)?navoid=(\d+)[^"]*)"[^>]*>(.*?)</a>', re.S)
STRIP = re.compile(r"<[^>]+>")


def waf_cookie(url):
    try:
        out = subprocess.run(["node", os.path.join(HERE, "waf_token.js"), url], capture_output=True, text=True, timeout=180)
        return json.loads(out.stdout.strip().splitlines()[-1])["cookie"]
    except (subprocess.TimeoutExpired, IndexError, KeyError, json.JSONDecodeError) as e:
        print(f"waf_token failed for {url}: {e} {getattr(e, 'stderr', '') or (out.stderr[-300:] if 'out' in dir() else '')}", file=sys.stderr)
        return ""


def fetch(url, cookie):
    page = get(url, {"Cookie": cookie})
    if "gokuProps" in page or len(page) < 3000:
        cookie = waf_cookie(url)
        page = get(url, {"Cookie": cookie})
    return page, cookie


def find_courses_nav(index):
    catoid = Counter(re.findall(r"catoid=(\d+)", index)).most_common(1)[0][0]
    links = [(href, nav, clean(html.unescape(STRIP.sub("", label)))) for href, cat, nav, label in NAV.findall(index) if cat == catoid]
    for pattern in (r"^courses?$", r"^course descriptions?$", r"^course (?:descriptions|information|listings?)", r"course"):
        for href, nav, label in links:
            if re.search(pattern, label, re.I):
                return catoid, nav
    raise SystemExit(f"no courses nav found; navoids: {[(n, l) for _, n, l in links][:40]}")


def scrape(base, rows):
    cookie = waf_cookie(base)
    index, cookie = fetch(base, cookie)
    catoid, navoid = find_courses_nav(index)
    print(f"  {base}: catoid {catoid} navoid {navoid}", file=sys.stderr)
    page_no, seen = 1, set()
    while True:
        url = urljoin(base, f"/content.php?catoid={catoid}&navoid={navoid}&cpage={page_no}")
        page, cookie = fetch(url, cookie)
        found = 0
        for _, coid, label in COURSE.findall(page):
            if coid in seen:
                continue
            seen.add(coid)
            found += 1
            text = clean(html.unescape(STRIP.sub("", label)))
            code, _, title = text.partition(" - ")
            if not title:
                code, _, title = text.partition(" – ")
            m = re.match(r"^([A-Z&]{2,6}(?:[ /-][A-Z]{1,4})?)", code)
            rows.append([code, title, "", m.group(1) if m else "", "", ""])
        print(f"  page {page_no}, {found} new ({len(rows)} total)", file=sys.stderr)
        if found == 0:
            break
        page_no += 1


def main(org, *bases):
    rows = []
    for base in bases:
        scrape(base, rows)
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
