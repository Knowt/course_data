# course_data

Course catalogs for the universities Knowt students belong to. One CSV per school, keyed by the school's org
domain, listing every course the school offers. These feed the `OrgCourseTable` in DynamoDB (shared by dev and
prod), which powers the course picker in Knowt.

## Layout

```
cleaned/     one finished CSV per org, e.g. cleaned/rutgers.edu.csv   ← the product of this repo
uncleaned/   raw inputs that have no cleaned output yet (a catalog PDF, exports without course codes)
scraper/     the scripts that produce cleaned/, plus sources.csv recording how each file was made
```

Every file in `cleaned/` has the same columns:

| Column | Example | Notes |
|---|---|---|
| `courseId` | `CS 112` | subject code, space, number. Unique per org; the import dedupes on it |
| `courseName` | `Data Structures` | |
| `courseCredits` | `3` or `1-4` | blank when the source has none |
| `courseSubject` | `Computer Science` | department or subject name; blank or the prefix when unknown |
| `courseLevel` | `Undergraduate` | `Graduate`, `Law`, a school name, or blank |
| `courseCampus` | `Hunter College` | only for multi-campus orgs such as CUNY, Rutgers, IU |

## How a school gets added

1. Find the school's catalog site and identify the provider. `python3 scraper/detect.py domains.txt` prints a guess
   for each domain; most schools run one of CourseLeaf, Acalog (Modern Campus), Coursedog, Banner, PeopleSoft or Kuali.
2. Run the matching script from `scraper/`. Each script's docstring shows its arguments; `scraper/README.md` has the
   table of providers and the gotchas (WAF challenges, required headers, term codes).
3. Check the output in `cleaned/<org>.csv`, then add a row to `scraper/sources.csv` with the exact script and
   arguments used. `scraper/run.sh <org>` replays that row later.
4. Run the import from Goliath's `apps/backend/school_generator`: `yarn build && node dist/index.cjs`. It reads
   `cleaned/` straight from this repo, which it expects as a sibling directory of the Goliath checkout (override
   with `COURSES_CSV_DIR=/path/to/cleaned`). Orgs already imported are skipped; set `REIMPORT_ORGS=a.edu,b.edu` to
   wipe and reload specific ones.

If a site blocks scripts, open it in a browser and copy the request that returns courses (DevTools → Copy as cURL).
Harvard, Princeton, Yale, Brown, UC Riverside and Boston College were all unlocked that way.

## Which schools to add next

Rank by Knowt usage, not enrollment: the `students` count on each prod `Organization` row says how many of our
users belong to that org. Cross it against `ls cleaned/` to find the largest orgs with no course list.

## History

The first ~120 schools were scraped in 2025 by Mihir (`mihirp11/course_data`, which this repo is forked from) with
scripts that were never checked in; their `sources.csv` rows say so. Everything since September 2026 has a script.
