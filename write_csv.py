"""Writes the processed CSV, one row per valid request.

This is the file you open in a spreadsheet to answer something like "show me
every 404". The JSON is for machines; this one is for people.
"""

import csv
import os

COLUMNS = [
    "timestamp", "ip", "method", "url", "status_code", "response_bytes",
    "response_time_ms", "category", "error_message",
]


def write_csv(records, path):
    """Write every record to the processed CSV. Returns the path, or None."""

    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        # newline="" is required by the csv module so it controls line endings.
        with open(path, "w", encoding="utf-8", newline="") as file:

            writer = csv.DictWriter(file, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()

            for record in records:
                row = {name: record.get(name, "") for name in COLUMNS}

                # None means the log did not record it. An empty cell says so
                # without putting the word None into a spreadsheet.
                for key, value in row.items():
                    if value is None:
                        row[key] = ""

                writer.writerow(row)

    except OSError as error:
        print(f"ERROR writing processed CSV: {error}")
        return None

    print(f"Processed CSV saved: {path}")

    return path
