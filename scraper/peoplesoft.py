"""PeopleSoft Campus Solutions "Browse Course Catalog" (COMMUNITY_ACCESS.SSS_BROWSE_CATLG.GBL), guest access.

usage: python3 peoplesoft.py <org> <GBL url> [referer]
Walks A-Z, expands every subject, and reads the course number / title rows. Stateful: one session, ICStateNum
comes back in each AJAX response.
"""
import html
import http.cookiejar
import re
import string
import sys
import urllib.parse
import urllib.request

from common import UA, clean, write_csv

FORM = {"ICAJAX": "1", "ICNAVTYPEDROPDOWN": "0", "ICType": "Panel", "ICElementNum": "0", "ICModelCancel": "0", "ICXPos": "0", "ICYPos": "0",
        "ResponsetoDiffFrame": "-1", "TargetFrameName": "None", "FacetPath": "None", "ICFocus": "", "ICSaveWarningFilter": "0", "ICChanged": "-1",
        "ICSkipPending": "0", "ICAutoSave": "0", "ICResubmit": "0", "ICActionPrompt": "false", "ICTypeAheadID": "", "ICBcDomData": "UnknownValue",
        "ICPanelName": "", "ICFind": "", "ICAddCount": "", "ICAppClsData": ""}
SUBJECT = re.compile(r"id='DERIVED_SSS_BCC_GROUP_BOX_1\$(\d+)'[^>]*>(.*?)</", re.S)
STRIP = re.compile(r"<[^>]+>")


class Session:
    def __init__(self, url, referer):
        self.url = url
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.opener.addheaders = list(UA.items()) + [("Referer", referer)]
        page = self.opener.open(url, timeout=60).read().decode("utf-8", "ignore")
        self.icsid = re.search(r"id=['\"]ICSID['\"] value=['\"]([^'\"]+)", page).group(1)
        self.state = re.search(r"id=['\"]ICStateNum['\"] value=['\"](\d+)", page).group(1)

    def click(self, action):
        data = urllib.parse.urlencode({**FORM, "ICStateNum": self.state, "ICAction": action, "ICSID": self.icsid}).encode()
        body = self.opener.open(urllib.request.Request(self.url, data=data), timeout=90).read().decode("utf-8", "ignore")
        state = re.search(r"<FIELD id='ICStateNum'>(\d+)</FIELD>", body) or re.search(r"ICStateNum\.value=(\d+);", body)
        if state:
            self.state = state.group(1)
        return html.unescape(body)


def parse(body):
    rows, subject = [], ""
    for label, kind, text in re.findall(r"class='PAGROUPBOXLABELINVISIBLE'[^>]*>(.*?)</td>|id='(CRSE_NBR|CRSE_TITLE)\$\d+'[^>]*>(.*?)</", body, re.S):
        text = clean(STRIP.sub("", label or text))
        if label:
            subject = text
        elif kind == "CRSE_NBR":
            prefix, _, name = subject.replace(" - ", " ", 1).partition(" ")
            name = name.strip().removeprefix(prefix + " ")
            rows.append([f"{prefix} {text}", "", "", name, "", ""])
        elif rows and not rows[-1][1]:
            rows[-1][1] = text
    return rows


def main(org, url, referer=None):
    s = Session(url, referer or url.split("/psc/")[0] + "/browse/")
    rows = []
    for letter in string.ascii_uppercase:
        s.click(f"DERIVED_SSS_BCC_SSR_ALPHANUM_{letter}")
        body = s.click("DERIVED_SSS_BCC_SSS_EXPAND_ALL$97$")
        found = parse(body)
        rows += found
        print(f"  {org}: {letter} -> {len(found)} courses ({len(rows)} total)", file=sys.stderr)
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
