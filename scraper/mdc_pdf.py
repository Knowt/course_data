"""Miami Dade College: parse the CurricUNET catalog PDF ("Download Catalog PDF" on mdc.curricunet.com/catalog).

usage: python3 mdc_pdf.py mdc.edu <catalog.pdf>     (needs `pip install pypdf`)
Course entries in the COURSE DESCRIPTIONS section look like "ACG2021 Financial Accounting 3.000 credits",
sometimes wrapped across two lines.
"""
import re
import sys

from pypdf import PdfReader

from common import clean, write_csv

CODE_LINE = re.compile(r"^([A-Z]{3}\d{4}[A-Z]?)\s+(.*)$")
CREDITS = re.compile(r"^(.*?)\s*(\d+\.\d{3}(?:\s*-\s*\d+\.\d{3})?)\s*credits\b", re.S)


def main(org, pdf):
    reader = PdfReader(pdf)
    pages = [p.extract_text() or "" for p in reader.pages]
    start = next(i for i, t in enumerate(pages) if t.lstrip().startswith("COURSE DESCRIPTIONS"))
    print(f"{org}: {len(pages)} pages, course descriptions start on page {start + 1}", file=sys.stderr)
    rows, pending = [], None
    for line in "\n".join(pages[start:]).splitlines():
        line = line.strip()
        m = CODE_LINE.match(line)
        if m:
            pending = [m.group(1), m.group(2)]
        elif pending and len(pending[1]) < 200:
            pending[1] += " " + line
        else:
            continue
        c = CREDITS.match(pending[1])
        if c:
            credits = re.sub(r"\.000", "", c.group(2)).replace(" ", "")
            rows.append([f"{pending[0][:3]} {pending[0][3:]}", clean(c.group(1)), credits, pending[0][:3], "", ""])
            pending = None
    write_csv(org, rows)


if __name__ == "__main__":
    main(*sys.argv[1:])
