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


def write_hourly_csv(records, path):
    """Write a small hour by hour summary with csv.writer.

    csv.writer takes plain lists instead of dictionaries, which suits a fixed
    three column table. zip() pairs the hour labels with their counts so the
    two lists cannot drift out of step, which is the mistake that version makes
    easy.
    """

    from validate import to_time

    os.makedirs(os.path.dirname(path), exist_ok=True)

    totals, errors = {}, {}

    for record in records:
        moment = to_time(record["timestamp"])

        if not moment:
            continue

        hour = moment.strftime("%H")
        totals[hour] = totals.get(hour, 0) + 1

        if record["status_code"] >= 400:
            errors[hour] = errors.get(hour, 0) + 1

    hours = sorted(totals)
    rows = list(zip(hours,
                    (totals[h] for h in hours),
                    (errors.get(h, 0) for h in hours)))

    try:
        with open(path, "w", encoding="utf-8", newline="") as file:

            writer = csv.writer(file)
            writer.writerow(["hour", "requests", "failed_requests"])
            writer.writerows(rows)

    except OSError as error:
        print(f"ERROR writing hourly CSV: {error}")
        return None

    print(f"Hourly summary saved: {path}")

    return path


def read_hourly(path):
    """Read the hourly summary back with csv.reader.

    csv.reader gives plain positional rows, which suits a three column table
    and is the counterpart to csv.writer above. The header is skipped with
    next() rather than by counting.
    """

    if not os.path.exists(path):
        return []

    rows = []

    with open(path, "r", encoding="utf-8", newline="") as file:

        reader = csv.reader(file)
        next(reader, None)          # the header written by writerow()

        for row in reader:
            if len(row) == 3:
                rows.append(tuple(row))

    return rows


def hourly_total(rows):
    """Add up the request column read back from the hourly CSV.

    Used to check that what was written matches what the analysis counted,
    which catches a silent off-by-one in the writer.
    """

    return sum(int(row[1]) for row in rows)
