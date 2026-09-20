"""Boston College public course search (services.bc.edu/PublicCourseInfoSched). Needs a reCAPTCHA token
(`personResponse`) and the cookies from a browser session that solved it: copy both from DevTools.

usage: BC_COOKIE='...' python3 bc.py bc.edu <personResponse> [term ...]   (terms like 2026FALL 2026SUMM)
"""
import concurrent.futures as cf
import html
import os
import re
import sys

from common import clean, get, write_csv

URL = ("https://services.bc.edu/PublicCourseInfoSched/courseinfoschedResults!displayInput.action?authenticated=false&keyword="
       "&presentTerm={term}&registrationTerm={term}&termsString={term}&selectedTerm={term}&selectedSort=&selectedSchool={school}"
       "&selectedSubject=0_All&selectedNumberRange=All&selectedLevel=&selectedMeetingDay=All&selectedMeetingTime=All"
       "&selectedCourseStatus=All&selectedCourseCredit=All&canvasSearchLink=&personResponse={token}"
       "&googleSiteKey=6LdwpLYqAAAAAC0aPahuR0xRdH2VZ14XFSdVpUZi")
SCHOOLS = ["3_LAW", "4_ADV", "5_SSW", "6_CSOM", "7_CSON", "8_LSOE", "9_STM", "116_MCBC", "2_MCAS"]
NAME = re.compile(r'class="course-name">([^<]*?)\s*\(([A-Z]{2,5})(\d{4})-\d+\)</strong>')
SCHOOL = re.compile(r"</a>\s*<br />([^<&]*)&nbsp;")
CREDITS = re.compile(r"Credits:</strong>\s*([\d.-]*)")
NOTICE = re.compile(r'<div class="notice">(.*?)</div>', re.S)


def courses(page):
    for chunk in page.split('<tr class="course"')[1:]:
        name, school, credits, notice = NAME.search(chunk), SCHOOL.search(chunk), CREDITS.search(chunk), NOTICE.search(chunk)
        if name:
            yield name.group(1), name.group(2), name.group(3), school.group(1) if school else "", credits.group(1) if credits else "", notice.group(1) if notice else ""


def fetch(term, school, subject, token, headers):
    url = URL.format(term=term, school=school, token=token).replace("selectedSubject=0_All", f"selectedSubject={subject}")
    page = get(url, headers, timeout=120)
    print(f"  {term} {school} {subject}: {len(page) // 1024}KB{' ERROR' if 'Search Results Error' in page else ''}", file=sys.stderr)
    return page


def main(org, token, *terms):
    headers = {"Cookie": os.environ.get("BC_COOKIE", "")}
    terms = terms or ("2026FALL", "2026SUMM")
    first = fetch(terms[0], SCHOOLS[0], "0_All", token, headers)
    subjects = sorted(set(re.findall(r'value="(\d+_[A-Z]+)"[^>]*id="selectedSubject', first)))
    jobs = [(term, school, "0_All") for term in terms for school in SCHOOLS]
    with cf.ThreadPoolExecutor(6) as ex:
        pages = dict(zip(jobs, ex.map(lambda j: fetch(*j, token, headers), jobs)))
        retry = [(term, school, s) for (term, school, _), page in pages.items() if "Search Results Error" in page
                 for s in subjects if s.startswith(school.split("_")[0] + "_")]
        print(f"{org}: {len(retry)} per-subject searches for schools over the result cap", file=sys.stderr)
        pages.update(zip(retry, ex.map(lambda j: fetch(*j, token, headers), retry)))
    rows = []
    for page in pages.values():
        for title, subject, number, school_name, credits, notice in courses(page):
            level = "Graduate" if "Graduate course" in notice else "Undergraduate" if "Undergraduate course" in notice else ""
            rows.append([f"{subject} {number}", clean(html.unescape(title)), credits, clean(html.unescape(school_name)), level, ""])
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
