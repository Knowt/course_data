"""CourseLeaf (Leepfrog) catalogs: catalog.<school>.edu with <div class="courseblock"> markup.

usage: python3 courseleaf.py <org> <catalog base url> [path-filter-regex]
Pages come from /sitemap.xml when present, otherwise a same-host crawl. Every page is parsed for course blocks.
"""
import concurrent.futures as cf
import html
import re
import sys
from urllib.parse import urljoin, urlparse

from common import clean, get as _get, write_csv

BOT_UA = {"User-Agent": "Mozilla/5.0 KnowtCourseBot/1.0"}
COOKIE = {}
INDEX_PATHS = ["/courses/", "/undergraduate/courses/", "/graduate/courses/", "/courses-az/", "/coursesaz/", "/course-descriptions/",
               "/the-college/courses/", "/undergraduate/coursesaz/", "/graduate/coursesaz/", "/course-catalog/", "/courses-a-z/"]


def get(url):
    page = _get(url, COOKIE)
    if "gokuProps" in page:
        from acalog import waf_cookie
        COOKIE["Cookie"] = waf_cookie(url)
        page = _get(url, COOKIE)
    return page

BLOCK = re.compile(r'<div class="courseblock[^"]*">(.*?)(?=<div class="courseblock[^"]*">|<div class="sc_sccoursedescs|</main>|</body>|$)', re.S)
DETAIL = lambda cls: re.compile(r'detail-' + cls + r'\b[^>]*>(?:<strong>)?(.*?)(?:</strong>)?</span>', re.S)
CODE, TITLE, HOURS = DETAIL("code"), DETAIL("title"), DETAIL("hours(?:_html)?")
BLOCK_TITLE = re.compile(r'class="courseblocktitle[^"]*"[^>]*>(.*?)</(?:h4|p|h3|div)>', re.S)
BLOCK_HOURS = re.compile(r'class="courseblockhours[^"]*"[^>]*>(.*?)</', re.S)
PAGE_TITLE = re.compile(r'<h1[^>]*class="page-title"[^>]*>(.*?)</h1>|<h1[^>]*>(.*?)</h1>', re.S)
CREDITS_TAIL = re.compile(r'[\s(]*(\d+(?:\.\d+)?(?:\s*(?:-|–|to|or)\s*\d+(?:\.\d+)?)?)\s*(?:credit hours?|credits?|units?|hours?|cr\.?|ch\.?|hrs?\.?|s\.h\.)\.?\)?\s*$', re.I)
CODE_HEAD = re.compile(r'^((?:[A-Z]{2,6}(?:[ &/-][A-Z]{1,6})?)\s?\d{1,5}[A-Z]{0,3}(?:\.\d{1,4})?[A-Z]?|\d{1,2}\.[0-9A-Z]{2,5}|[A-Z]{2,6}-\d{2,4}[A-Z]?)\s*[.:\-–]?\s+(.+)$')
STRIP = re.compile(r"<[^>]+>")


def text(s):
    return clean(html.unescape(STRIP.sub(" ", s or "")))


def parse_block(block):
    c, t, h = CODE.search(block), TITLE.search(block), HOURS.search(block)
    if c and t:
        return text(c.group(1)), text(t.group(1)), credits(text(h.group(1)) if h else "")
    bt = BLOCK_TITLE.search(block)
    if not bt:
        return None
    line = text(bt.group(1))
    hrs = BLOCK_HOURS.search(block)
    cred = credits(text(hrs.group(1))) if hrs else ""
    m = CREDITS_TAIL.search(line)
    if m:
        cred = cred or m.group(1)
        line = line[: m.start()].strip()
    m = CODE_HEAD.match(line)
    if not m:
        return None
    return m.group(1), m.group(2).strip(" .-–:"), cred


def credits(s):
    m = CREDITS_TAIL.search(" " + s) or re.match(r"^\s*(\d+(?:\.\d+)?(?:\s*(?:-|–|to|or)\s*\d+(?:\.\d+)?)?)", s)
    return m.group(1).replace("–", "-").replace(" to ", "-").replace(" or ", "-").replace(" ", "") if m else ""


def level_from(url, code):
    path = urlparse(url).path.lower()
    if "undergrad" in path:
        return "Undergraduate"
    if "graduate" in path or "/grad/" in path:
        return "Graduate"
    return ""


def parse_page(url, page):
    rows = []
    blocks = BLOCK.findall(page)
    if not blocks:
        return rows
    pt = PAGE_TITLE.search(page)
    subject = text(pt.group(1) or pt.group(2)) if pt else ""
    if not subject or re.search(r"catalog|bulletin", subject, re.I):
        tt = re.search(r"<title>(.*?)</title>", page, re.S)
        subject = text(tt.group(1)).split("|")[0].split(" - ")[0].split("<")[0] if tt else subject
    subject = re.sub(r"\s*\([A-Z0-9 &/-]+\)\s*$", "", subject)
    for b in blocks:
        parsed = parse_block(b)
        if parsed:
            code, title, cred = parsed
            rows.append([code, title, cred, subject, level_from(url, code), ""])
    return rows


def sitemap_urls(base):
    body = get(urljoin(base, "/sitemap.xml"))
    if "<loc>" not in body:
        body = _get(urljoin(base, "/sitemap.xml"), BOT_UA)
    if not body or "<loc>" not in body:
        return []
    urls = re.findall(r"<loc>(.*?)</loc>", body)
    nested = [u for u in urls if u.endswith(".xml")]
    for n in nested:
        urls += re.findall(r"<loc>(.*?)</loc>", get(n) or "")
    return [u for u in urls if not u.endswith(".xml")]


def crawl_urls(base, limit=1500):
    host = urlparse(base).netloc
    seeds = [urljoin(base, p) for p in INDEX_PATHS if "courseblock" in get(urljoin(base, p)) or 'href="' in get(urljoin(base, p)) and len(get(urljoin(base, p))) > 5000]
    seeds = [u for u in seeds if "<title>" in get(u) and "404" not in get(u)[:2000]]
    prefixes = tuple(seeds) if seeds else (base,)
    print(f"crawl seeds: {seeds or [base]}", file=sys.stderr)
    seen, queue, pages = set(), list(seeds) or [base], {}
    with cf.ThreadPoolExecutor(8) as ex:
        while queue and len(seen) < limit:
            batch = [u for u in queue[:32] if u not in seen]
            queue = queue[32:]
            for u in batch:
                seen.add(u)
            for u, page in zip(batch, ex.map(get, batch)):
                pages[u] = page
                for href in re.findall(r'href="([^"#?]+)"', page):
                    full = urljoin(u, href).split("#")[0]
                    if urlparse(full).netloc == host and full.endswith("/") and full.startswith(prefixes) and full not in seen:
                        queue.append(full)
    return pages


def main(org, base, path_filter=None):
    urls = sitemap_urls(base)
    host = urlparse(base).netloc
    if base.startswith("http://"):
        urls = [u.replace("https://", "http://", 1) for u in urls]
    urls = [u for u in urls if urlparse(u).netloc == host]
    if path_filter:
        urls = [u for u in urls if re.search(path_filter, u)]
    if urls:
        print(f"{org}: {len(urls)} sitemap urls", file=sys.stderr)
        with cf.ThreadPoolExecutor(8) as ex:
            pages = dict(zip(urls, ex.map(get, urls)))
    else:
        print(f"{org}: no sitemap, crawling", file=sys.stderr)
        pages = crawl_urls(base)
    rows = []
    for u, page in pages.items():
        rows += parse_page(u, page)
    print(f"{org}: {len(pages)} pages, {len(rows)} course blocks", file=sys.stderr)
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
