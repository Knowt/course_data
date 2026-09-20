"""Ellucian Banner 9 self-service course search (…/StudentRegistrationSsb/ssb/courseSearch), unioned over terms.

usage: python3 banner.py <org> <ssb base url, e.g. https://registrationssb.ucr.edu/StudentRegistrationSsb> <term> [term ...]
Term codes come from the site's term dropdown (UCR: 202640 = Fall 2026).
"""
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request

from common import UA, write_csv

PAGE = 500


def session(base):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = list(UA.items()) + [("X-Requested-With", "XMLHttpRequest"), ("Referer", f"{base}/ssb/courseSearch/courseSearch")]
    page = opener.open(f"{base}/ssb/courseSearch/courseSearch", timeout=30).read().decode("utf-8", "ignore")
    token = re.search(r'name="synchronizerToken" content="([^"]+)"', page)
    return opener, token.group(1) if token else ""


def call(opener, token, url, data=None):
    req = urllib.request.Request(url, data=data, headers={"X-Synchronizer-Token": token})
    return opener.open(req, timeout=60).read().decode("utf-8", "ignore")


def term_courses(base, term):
    opener, token = session(base)
    sid = f"knowt{term}"
    call(opener, token, f"{base}/ssb/term/search?mode=courseSearch", urllib.parse.urlencode({"term": term, "studyPath": "", "studyPathText": "", "startDatepicker": "", "endDatepicker": "", "uniqueSessionId": sid}).encode())
    offset, rows, total = 0, [], None
    while total is None or offset < total:
        url = f"{base}/ssb/courseSearchResults/courseSearchResults?txt_term={term}&uniqueSessionId={sid}&pageOffset={offset}&pageMaxSize={PAGE}&sortColumn=subjectDescription&sortDirection=asc"
        result = json.loads(call(opener, token, url))
        total = result.get("totalCount") or 0
        for c in result.get("data") or []:
            lo, hi = c.get("creditHourLow"), c.get("creditHourHigh")
            cred = "" if lo is None else (str(lo) if hi in (None, lo) else f"{lo}-{hi}")
            rows.append([f"{c.get('subject', '')} {c.get('courseNumber', '')}", c.get("courseTitle") or "", cred, c.get("subjectDescription") or "", "", ""])
        offset += PAGE
    print(f"  term {term}: {len(rows)} of {total}", file=sys.stderr)
    return rows


def main(org, base, *terms):
    rows = []
    for term in terms:
        rows += term_courses(base.rstrip("/"), term)
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
