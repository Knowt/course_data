"""Michigan LSA Course Bulletin (webapps.lsa.umich.edu/CrsMaint/Public/CB_PublicBulletin.aspx), ASP.NET WebForms.

usage: python3 umich.py umich.edu [term ...]   (default: Fall 2026, Spring 2026, Winter 2026)
For each level (ug, gr) and term: load the page, post back the term change to get that term's subject list and
viewstate, then run one "View All" search per subject in parallel.
"""
import concurrent.futures as cf
import html
import http.cookiejar
import re
import sys
import urllib.parse
import urllib.request

from common import UA, clean, write_csv

URL = "https://webapps.lsa.umich.edu/CrsMaint/Public/CB_PublicBulletin.aspx?crselevel={level}"
LISTING = re.compile(r"<tr class='listing'.*?<b>\s*([A-Z&]+\s+\d+[A-Z]*)[.:]?\s*(.*?)</b>(?:.*?<i>(.*?)</i>)?", re.S)
LEVELS = {"ug": "Undergraduate", "grad": "Graduate"}
FIELDS = {"ctl00$contentMain$ddlAttr": "", "ctl00$contentMain$ddlSubject": "", "ctl00$contentMain$ddlDept": "",
          "ctl00$contentMain$ddlPage": "9999", "ctl00$contentMain$chbShowDescr": "on"}


def opener():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = list(UA.items())
    return op


def post(level, data):
    url = URL.format(level=level)
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), headers={"Referer": url})
    return opener().open(req, timeout=180).read().decode("utf-8", "ignore")


def hidden_fields(page):
    return dict(re.findall(r'<input type="hidden" name="([^"]+)"[^>]*value="([^"]*)"', page))


def prepare(level, term):
    page = opener().open(URL.format(level=level), timeout=60).read().decode("utf-8", "ignore")
    page = post(level, {**hidden_fields(page), **FIELDS, "__EVENTTARGET": "ctl00$contentMain$ddlTerm",
                        "ctl00$contentNavBar$ddlCreditType": level, "ctl00$contentMain$ddlTerm": term})
    select = re.search(r'name="ctl00\$contentMain\$ddlSubject"[^>]*>(.*?)</select>', page, re.S)
    subjects = [s for s in re.findall(r'<option[^>]*value="([^"]*)"', select.group(1))] if select else []
    return hidden_fields(page), [s for s in subjects if s]


def search(level, term, hidden, subject):
    try:
        page = post(level, {**hidden, **FIELDS, "ctl00$contentNavBar$ddlCreditType": level, "ctl00$contentMain$ddlTerm": term,
                            "ctl00$contentMain$ddlSubject": subject, "ctl00$contentMain$btnSearch": "Search"})
    except Exception as e:
        print(f"FAILED {level} {subject} {term}: {e}", file=sys.stderr)
        return []
    rows = []
    for code, title, info in LISTING.findall(page):
        m = re.search(r"\((\d+(?:\s*-\s*\d+)?)\)", info or "")
        code = clean(html.unescape(code))
        rows.append([code, clean(html.unescape(re.sub(r"<[^>]+>", "", title))), m.group(1).replace(" ", "") if m else "", code.split()[0], LEVELS[level], ""])
    return rows


def main(org, *terms):
    terms = terms or ("2610", "2580", "2570")
    rows = []
    for level in LEVELS:
        for term in terms:
            hidden, subjects = prepare(level, term)
            with cf.ThreadPoolExecutor(8) as ex:
                found = sum(ex.map(lambda s: search(level, term, hidden, s), subjects), [])
            rows += found
            print(f"{org}: {level} {term}, {len(subjects)} subjects, {len(found)} rows ({len(rows)} total)", file=sys.stderr)
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
