#!/usr/bin/env python3
"""
Scan all Salesforce custom field definitions and identify fields that are not
referenced anywhere else in the metadata (layouts, flows, Apex, profiles,
permission sets, LWC, flexipages, triggers, VF pages, etc.).

Strategy: load all non-field-definition metadata files into memory once,
then check each field API name against the combined corpus.

Output: scripts/unreferenced_fields.csv
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
METADATA_ROOT = REPO_ROOT / "force-app" / "main" / "default"
OBJECTS_DIR = METADATA_ROOT / "objects"
OUTPUT_CSV = REPO_ROOT / "scripts" / "unreferenced_fields.csv"

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
    """Read every metadata file (except field definitions and binaries) into a
    dict keyed by relative path.  Returns { rel_path: file_contents_str }."""
    corpus = {}
    for fpath in METADATA_ROOT.rglob("*"):
        if not fpath.is_file():
            continue
        if fpath.suffix.lower() in SKIP_EXTENSIONS:
            continue
        # Skip field definition files — those are what we're checking *for*
        if "/fields/" in str(fpath) and fpath.name.endswith(".field-meta.xml"):
            continue
        try:
            corpus[str(fpath.relative_to(REPO_ROOT))] = fpath.read_text(errors="replace")
        except Exception:
            pass
    return corpus


def main():
    print(f"Metadata root : {METADATA_ROOT}")
    print(f"Objects dir   : {OBJECTS_DIR}")
    print()

    fields = collect_fields()
    print(f"Total field definitions found: {len(fields)}")
    print()

    print("Loading reference corpus (all non-field metadata files) …")
    corpus = load_reference_corpus()
    print(f"Loaded {len(corpus)} files into memory.")
    print()

    # Concatenate into one big string for fast substring search.
    # This is ~50-100 MB which fits comfortably in RAM.
    big_text = "\n".join(corpus.values())
    print(f"Corpus size: {len(big_text):,} characters")
    print()

    unreferenced: list[tuple[str, str, Path]] = []
    referenced_count = 0

    for i, (key, field_path) in enumerate(fields.items(), 1):
        _, field_name = key.split(".", 1)
        if field_name in big_text:
            referenced_count += 1
        else:
            obj = key.split(".", 1)[0]
            unreferenced.append((obj, field_name, field_path))

        if i % 100 == 0 or i == len(fields):
            print(f"  Checked {i}/{len(fields)} fields …")

    unreferenced.sort(key=lambda t: (t[0], t[1]))

    with open(OUTPUT_CSV, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Object", "Field", "FieldPath"])
        for obj, fld, path in unreferenced:
            rel_path = path.relative_to(REPO_ROOT)
            writer.writerow([obj, fld, str(rel_path)])

    print()
    print("=" * 60)
    print(f"  Total fields scanned  : {len(fields)}")
    print(f"  Referenced            : {referenced_count}")
    print(f"  UNREFERENCED          : {len(unreferenced)}")
    print("=" * 60)
    print()

    by_object = defaultdict(list)
    for obj, fld, _ in unreferenced:
        by_object[obj].append(fld)

    if unreferenced:
        print("Breakdown by object:")
        for obj in sorted(by_object):
            flds = by_object[obj]
            print(f"  {obj}: {len(flds)} unreferenced field(s)")
            for f in sorted(flds):
                print(f"    - {f}")
        print()
        print(f"CSV written to: {OUTPUT_CSV}")
    else:
        print("All fields are referenced somewhere in the metadata.")


if __name__ == "__main__":
    main()
