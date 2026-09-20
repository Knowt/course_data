import concurrent.futures as cf, re, sys, urllib.request, json
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) KnowtCourseBot/1.0"}
MARKERS = [
    ("courseleaf", re.compile(r"courseleaf|/ribbit/|class=\"courseblock", re.I)),
    ("acalog", re.compile(r"acalog|content\.php\?catoid=|preview_course_nopop", re.I)),
    ("kuali", re.compile(r"kuali\.co|kuali", re.I)),
    ("coursedog", re.compile(r"coursedog", re.I)),
    ("cleancatalog", re.compile(r"cleancatalog", re.I)),
    ("smartcatalog", re.compile(r"smartcatalogiq|smartcatalog", re.I)),
    ("clss", re.compile(r"catalog\.(academic)?", re.I)),
]
def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.geturl(), r.read(400000).decode("utf-8", "ignore")
    except Exception as e:
        return None, ""
def classify(html):
    for name, rx in MARKERS[:-1]:
        if rx.search(html): return name
    return "unknown"
def probe(domain):
    cands = [f"https://catalog.{domain}/", f"https://catalogs.{domain}/", f"https://bulletin.{domain}/", f"https://{domain}/catalog/",
             f"https://www.{domain}/catalog/", f"https://catalog.{domain}/courses/", f"https://{domain}/academics/catalog/"]
    results = []
    for u in cands:
        final, html = fetch(u)
        if final and html:
            prov = classify(html)
            results.append((u, final, prov, len(html)))
            if prov != "unknown": break
    return domain, results
if __name__ == "__main__":
    domains = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
    with cf.ThreadPoolExecutor(12) as ex:
        for domain, results in ex.map(probe, domains):
            best = next((r for r in results if r[2] != "unknown"), results[0] if results else None)
            print(json.dumps({"domain": domain, "provider": best[2] if best else "none", "url": best[1] if best else None, "tried": len(results)}))
