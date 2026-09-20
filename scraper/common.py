import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
HEADER = ["courseId", "courseName", "courseCredits", "courseSubject", "courseLevel", "courseCampus"]
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cleaned")


def get(url, headers=None, data=None, retries=3, timeout=20):
    err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})}, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            err = e
            if 400 <= e.code < 500:
                break
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            err = e
            time.sleep(2 * (attempt + 1))
    print(f"FAILED {url}: {err}", file=sys.stderr)
    return ""


def get_json(url, headers=None, data=None):
    body = get(url, headers, data)
    return json.loads(body) if body else None


def clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def write_csv(org, rows):
    deduped = {}
    for row in rows:
        code = clean(row[0]).upper()
        if code and code not in deduped:
            deduped[code] = [code] + [clean(x) for x in row[1:]]
    path = os.path.join(OUT_DIR, f"{org}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(deduped.values())
    print(f"{org}: wrote {len(deduped)} courses ({len(rows) - len(deduped)} duplicates) -> {path}")
    return path
