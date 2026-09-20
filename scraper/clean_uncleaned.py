"""One-off column mappings for the raw CSVs Mihir scraped but never cleaned."""
import csv
import os
import re
import sys

from common import write_csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rows(path):
    return list(csv.DictReader(open(f"{ROOT}/uncleaned/{path.removeprefix('uncleaned/')}", encoding="utf-8-sig")))


def credits(s):
    m = re.search(r"(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)", s or "")
    return m.group(1).replace(" ", "") if m else ""


def msu():
    return [[r["course_code"], r["course_name"], "", r["subject"].split(" - ", 1)[-1], "", ""] for r in rows("msu_courses.csv")]


def rit():
    out = []
    for level, path in (("Graduate", "rit_graduate.csv"), ("Undergraduate", "rit_undergraduate.csv")):
        for r in rows(path):
            m = re.match(r"^\s*(\d+[A-Z]?)\s+(.*)$", r["course_title"])
            if not m:
                continue
            out.append([f"{r['course_code']} {m.group(1)}", m.group(2), credits(r["credits"]), re.sub(r"\s*\(.*\)$", "", r["department"]), level, ""])
    return out


def pdx():
    return [[r["course_code"].upper(), r["course_title"], credits(r["course_credits"]), r["department"].split(" - ", 1)[-1], "", ""] for r in rows("pdx.csv")]


def umass():
    return [[r["code"].replace("-", " "), r["title"], "", r["department"], r["level"], ""] for r in rows("uncleaned/umass.csv")]


def nvcc():
    return [[r["course_code"], r["course_name"], credits(r["credits"]), r["subject"], "", ""] for r in rows("nvcc.csv")]


def valenciacollege():
    return [[r["course_code"], r["course_title"].rstrip(".").title(), credits(r["credits"]), r["department"].split(": ", 1)[-1], "", ""] for r in rows("valenciacollege.csv")]


def northwestern():
    out = []
    for level, path in (("Undergraduate", "northwestern_undergrad.csv"), ("Graduate", "northwestern_graduate.csv"), ("Law", "northwestern_law.csv"), ("", "northwestern_sps.csv")):
        for r in rows(path):
            out.append([r["course_code"], r["course_title"], credits(r["credits"]), re.sub(r"\s*\(.*\)$", "", r["department"].split(" - ", 1)[-1]), level, ""])
    return out


def rowan():
    return [[r["course_code"], r["course_name"], credits(r["credits"]), r["subject"], "", ""] for r in rows("rowan.csv")]


STANDARD = {
    "shsu.edu": [("Graduate", "shsu_graduate.csv"), ("Undergraduate", "shsu_undergraduate.csv")],
    "towson.edu": [("Graduate", "towson_graduate.csv"), ("Undergraduate", "towson_undergrad.csv")],
    "uab.edu": [("Graduate", "uab_graduate.csv"), ("Undergraduate", "uab_undergrad.csv")],
    "odu.edu": [("", "odu.csv")],
    "uncg.edu": [("", "uncg.csv")],
}


def standard(org):
    out = []
    for level, path in STANDARD[org]:
        for r in rows(path):
            dept = re.sub(r"\s*\([A-Z& -]+\)$", "", r["department"])
            dept = re.sub(r"^[A-Z&]+\s*-\s*", "", dept).replace(" Courses", "")
            out.append([r["course_code"], r["course_title"].title() if r["course_title"].isupper() else r["course_title"], credits(r["credits"]), dept, r.get("level") or level, ""])
    return out


def iu():
    return [[r["code"], r["title"].title(), credits(r["credits"]), r["department"], "", r["campus"]] for r in rows("uncleaned/indiana_university.csv")]


def bmcc():
    return [[r["course_code"], r["course_title"], credits(r["credits"]), "", "", "Borough of Manhattan Community College"] for r in rows("bmcc.csv")]


if __name__ == "__main__":
    for name in sys.argv[1:] or ["msu", "rit", "pdx", "umass", "nvcc", "valenciacollege"]:
        if name in STANDARD:
            write_csv(name, standard(name))
            continue
        org = {"msu": "msu.edu", "rit": "rit.edu", "pdx": "pdx.edu", "umass": "umass.edu", "nvcc": "nvcc.edu", "valenciacollege": "valenciacollege.edu", "bmcc": "_cuny_bmcc", "northwestern": "northwestern.edu", "rowan": "rowan.edu", "iu": "iu.edu"}[name]
        write_csv(org, globals()[name]())
