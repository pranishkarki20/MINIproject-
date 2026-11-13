"""Builds and writes the structured JSON report.

The dataset citation goes in here, not only in the README, so a number can
never be separated from where it came from.
"""

import json
import os
from datetime import datetime

DATASET = {
    "title": "Web Server Log Dataset",
    "author": "Anonim",
    "publisher": "Zenodo",
    "published": "2026-05-03",
    "doi": "10.5281/zenodo.20001206",
    "url": "https://zenodo.org/records/20001206",
    "download": ("https://zenodo.org/api/records/20001206/files/"
                 "organization-x.zip/content"),
    "license": "MIT",
    "file_in_archive": "organization-x/log/apache2/web-access.log.1",
    "description": (
        "Raw Apache access log from a live public sector web server, "
        "published for research into reconstructing web application attacks. "
        "Copied out of the archive unchanged."
    ),
}


def build_report(path, sections):
    """Put the citation, the run time and the analysis into one dictionary."""

    if path.lower().endswith(".csv"):
        fmt = "CSV log export"
    else:
        fmt = "Apache Combined Log Format (text access log)"

    return {
        "report": "Application Log Monitoring and Error Analysis",
        "course": "25PCCS202 Python Programming, Mini Project 4, Unit IV",
        "dataset": dict(DATASET, file=path, format=fmt),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **sections,
    }


def write_json(report, path):
    """Write the report as JSON. Returns the path, or None on failure."""

    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

    except OSError as error:
        print(f"ERROR writing JSON report: {error}")
        return None

    except (TypeError, ValueError) as error:
        # Something in the report is not JSON, such as a datetime object.
        print(f"ERROR: value JSON cannot write: {error}")
        return None

    print(f"JSON report saved: {path}")

    return path
