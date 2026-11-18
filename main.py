"""Application Log Monitoring and Error Analysis System.

Mini Project 4, Unit IV (File Handling, CSV, JSON, Exception Handling)
Course 25PCCS202 Python Programming

Reads a real Apache web server log, works out which requests succeeded and
which failed, writes a processed CSV and a JSON report, reads that JSON back
to build a readable summary, then lets the user search the records.

    python main.py

Dataset: Web Server Log Dataset, Zenodo, DOI 10.5281/zenodo.20001206, MIT
licence. Details, fields, results and limitations in README.md.
"""

import os

import analyse
import make_summary
import pandas_view
import read_log
import search
import validate
import write_csv
import write_json

INPUT_FILE = os.path.join("data", "web-access.log.1")
OUTPUT_DIR = "output"
PROCESSED_CSV = os.path.join(OUTPUT_DIR, "processed_logs.csv")
HOURLY_CSV = os.path.join(OUTPUT_DIR, "hourly_summary.csv")
SUMMARY_JSON = os.path.join(OUTPUT_DIR, "summary_report.json")
FINAL_TEXT = os.path.join(OUTPUT_DIR, "final_summary.txt")
RUN_HISTORY = os.path.join(OUTPUT_DIR, "run_history.txt")


def process(path):

    records = []
    rejected = []

    try:
        entries = read_log.read_log(path)

        for number, fields, error in entries:

            try:
                if error:
                    raise ValueError(error)

                records.append(validate.build_record(number, fields))

            except (ValueError, TypeError) as problem:
                rejected.append((number, str(problem)))

        else:
            print(f"Log reading completed: {path} ({len(entries)} lines)")

    except FileNotFoundError:
        print(f"ERROR: Dataset not found: {path}")
        print("Download it into the data folder. See README.md, section 2.")
        return None, None

    except PermissionError:
        print("ERROR: Permission denied while reading the dataset.")
        return None, None

    except UnicodeDecodeError:
        print("ERROR: The dataset is not readable text.")
        return None, None

    except ValueError as problem:
        print(f"ERROR: {problem}")
        return None, None

    finally:
        print("Dataset reading stage finished.")

    return records, rejected


def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    records, rejected = process(INPUT_FILE)

    if records is None:
        return 1

    if not records:
        print("ERROR: No valid records were read. Nothing to report.")
        return 1

    sections = analyse.analyse(records, rejected)

    if write_csv.write_csv(records, PROCESSED_CSV) is None:
        return 1

    write_csv.write_hourly_csv(records, HOURLY_CSV)

    # Read the hourly file back with csv.reader and check it adds up to the
    # number of records analysed. A writer that dropped or duplicated a row
    # would otherwise go unnoticed.
    hourly_rows = write_csv.read_hourly(HOURLY_CSV)
    sections["hourly_self_check"] = {
        "hours_written": len(hourly_rows),
        "requests_in_file": write_csv.hourly_total(hourly_rows),
        "requests_analysed": len(records),
        "matches": write_csv.hourly_total(hourly_rows) == len(records),
    }

    # The pandas view is optional. Without it the project is complete, with it
    # the report also carries the Unit IV CSV and JSON round trip through
    # pandas. ImportError is expected on a machine that has no pandas.
    try:
        sections["pandas_view"] = pandas_view.summarise(PROCESSED_CSV)
    except ImportError:
        print("pandas is not installed, skipping the pandas view.")
        sections["pandas_view"] = None
    except (OSError, ValueError) as error:
        print(f"pandas view failed, continuing without it: {error}")
        sections["pandas_view"] = None

    report = write_json.build_report(INPUT_FILE, sections)

    if write_json.write_json(report, SUMMARY_JSON) is None:
        return 1

    saved = make_summary.read_report(SUMMARY_JSON)

    if saved is None:
        return 1

    text = make_summary.make_text(saved)
    make_summary.write_text(text, FINAL_TEXT)

    # Append this run to the history so repeat runs can be compared.
    make_summary.record_run(saved, RUN_HISTORY)

    search.search(records)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
