
import csv
import os

COLUMNS = [
    "timestamp", "ip", "method", "url", "status_code", "response_bytes",
    "response_time_ms", "category", "error_message",
]


def write_csv(records, path):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8", newline="") as file:

            writer = csv.DictWriter(file, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()

            for record in records:
                row = {name: record.get(name, "") for name in COLUMNS}

                for key, value in row.items():
                    if value is None:
                        row[key] = ""

                writer.writerow(row)

    except OSError as error:
        print(f"ERROR writing processed CSV: {error}")
        return None

    print(f"Processed CSV saved: {path}")

    return path
