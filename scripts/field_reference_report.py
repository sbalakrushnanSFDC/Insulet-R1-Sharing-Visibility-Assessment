#!/usr/bin/env python3
"""
Generate a detailed report of all Salesforce custom fields and where they are
referenced in the metadata (layouts, flows, Apex, profiles, permission sets,
LWC, flexipages, triggers, VF pages, etc.).

Output CSV: Object, Field, ReferencesCount, ReferencedDetails
- ReferencesCount: total number of occurrences across all metadata files
- ReferencedDetails: semicolon-separated list of "file_path (count)" for each
  file where the field appears, sorted by count descending
"""

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
METADATA_ROOT = REPO_ROOT / "force-app" / "main" / "default"
OBJECTS_DIR = METADATA_ROOT / "objects"
OUTPUT_CSV = REPO_ROOT / "scripts" / "field_reference_report.csv"

SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff", ".woff2", ".ttf", ".eot"}


def collect_fields():
    """Return dict { 'ObjectName.FieldAPIName': Path } for every field definition."""
    fields = {}
    for field_file in sorted(OBJECTS_DIR.rglob("*/fields/*.field-meta.xml")):
        object_name = field_file.parent.parent.name
        field_name = field_file.name.replace(".field-meta.xml", "")
        key = f"{object_name}.{field_name}"
        fields[key] = field_file
    return fields


def load_reference_corpus():
    """Read every metadata file (except field definitions and binaries) into
    dict { rel_path: file_contents_str }."""
    corpus = {}
    for fpath in METADATA_ROOT.rglob("*"):
        if not fpath.is_file():
            continue
        if fpath.suffix.lower() in SKIP_EXTENSIONS:
            continue
        if "/fields/" in str(fpath) and fpath.name.endswith(".field-meta.xml"):
            continue
        try:
            corpus[str(fpath.relative_to(REPO_ROOT))] = fpath.read_text(errors="replace")
        except Exception:
            pass
    return corpus


def count_occurrences(text: str, substring: str) -> int:
    """Count non-overlapping occurrences of substring in text.
    Note: may over-count when a field name is a substring of another
    (e.g. Type__c inside Contract_Type__c)."""
    count = 0
    start = 0
    while True:
        pos = text.find(substring, start)
        if pos == -1:
            break
        count += 1
        start = pos + len(substring)
    return count


def main():
    print(f"Metadata root : {METADATA_ROOT}")
    print(f"Objects dir   : {OBJECTS_DIR}")
    print()

    fields = collect_fields()
    print(f"Total field definitions found: {len(fields)}")
    print()

    print("Loading reference corpus …")
    corpus = load_reference_corpus()
    print(f"Loaded {len(corpus)} files.")
    print()

    # Build report: for each field, count refs per file
    report: list[tuple[str, str, int, str]] = []

    for i, (key, _) in enumerate(fields.items(), 1):
        object_name, field_name = key.split(".", 1)

        file_counts: dict[str, int] = {}
        for rel_path, content in corpus.items():
            cnt = count_occurrences(content, field_name)
            if cnt > 0:
                file_counts[rel_path] = cnt

        total = sum(file_counts.values())
        # Format: "file1 (n1); file2 (n2); ..." sorted by count desc
        details = "; ".join(
            f"{path} ({n})"
            for path, n in sorted(file_counts.items(), key=lambda x: -x[1])
        ) if file_counts else ""

        report.append((object_name, field_name, total, details))

        if i % 100 == 0 or i == len(fields):
            print(f"  Processed {i}/{len(fields)} fields …")

    # Sort by Object, then by ReferencesCount descending, then Field
    report.sort(key=lambda r: (r[0], -r[2], r[1]))

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Object", "Field", "ReferencesCount", "ReferencedDetails"])
        for obj, fld, cnt, details in report:
            writer.writerow([obj, fld, cnt, details])

    print()
    print("=" * 60)
    print(f"  Report written to: {OUTPUT_CSV}")
    print("=" * 60)

    # Summary stats
    unreferenced = sum(1 for r in report if r[2] == 0)
    print(f"\nSummary:")
    print(f"  Total fields   : {len(report)}")
    print(f"  Referenced     : {len(report) - unreferenced}")
    print(f"  Unreferenced   : {unreferenced}")
    top = sorted([r for r in report if r[2] > 0], key=lambda r: -r[2])[:5]
    if top:
        print(f"\n  Top 5 most referenced fields:")
        for obj, fld, cnt, _ in top:
            print(f"    {obj}.{fld}: {cnt} references")


if __name__ == "__main__":
    main()
