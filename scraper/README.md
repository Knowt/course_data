# Course catalog scrapers

`sources.csv` is the record of how every file in `../cleaned/` was produced: one row per org with the script and the arguments used. Replay one with `./run.sh <org>`. Rows with an empty script are Mihir's original 2025 scrapes, whose scripts were never checked in.

Output goes to `../cleaned/<org>.csv` with the columns `courseId,courseName,courseCredits,courseSubject,courseLevel,courseCampus`. Copy the file into `apps/backend/school_generator/src/csv/courses/` in Goliath and run the course import there.

## Scripts by catalog provider

| Script | Provider | How to spot it | Args |
|---|---|---|---|
| `courseleaf.py` | CourseLeaf (Leepfrog) | `catalog.<school>.edu` with `<div class="courseblock">` | catalog base URL |
| `acalog.py` | Acalog / Modern Campus | `content.php?catoid=N&navoid=M` URLs | catalog index URL, one per catoid if undergrad and grad are separate |
| `coursedog.py` | Coursedog | Nuxt SPA, `app.coursedog.com` in the JS | catalog host |
| `fose.py` | CourseLeaf FOSE course search | `/api/?page=fose&route=search` | host plus term codes (`srcdb`) from the site's term dropdown |
| `kuali.py` | Kuali | `<school>.kuali.co` | tenant base URL |
| `asu.py`, `harvard.py`, `princeton.py` | one-off public APIs | | see the docstring in each |
| `clean_uncleaned.py` | none | column mappings for raw CSVs in `../uncleaned/` | raw file name |

`detect.py <domains file>` probes a list of domains and prints the provider for each.

## Gotchas

- Acalog sites and some CourseLeaf sites sit behind an AWS WAF JavaScript challenge. `waf_token.js` solves it with Playwright and the Python scripts call it automatically; it needs `NODE_PATH` pointing at a `node_modules` that has `playwright` (Goliath's root works).
- Coursedog's search API only answers when `Origin` and `Referer` are set to the catalog host.
- If a site rejects the scripts outright, open the page in a browser, use DevTools "Copy as cURL" on the request that returns courses, and build from that. Harvard, Princeton, Yale and Brown were all unlocked this way.
- Most catalogs list a course once per term or section. `write_csv` dedupes on `courseId`, so high duplicate counts in the log are normal.
