
import os

import analyse
import make_summary
import read_log
import search
import validate
import write_csv
import write_json

INPUT_FILE = os.path.join("data", "web-access.log.1")
OUTPUT_DIR = "output"
PROCESSED_CSV = os.path.join(OUTPUT_DIR, "processed_logs.csv")
SUMMARY_JSON = os.path.join(OUTPUT_DIR, "summary_report.json")
FINAL_TEXT = os.path.join(OUTPUT_DIR, "final_summary.txt")


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

    report = write_json.build_report(INPUT_FILE, sections)

    if write_json.write_json(report, SUMMARY_JSON) is None:
        return 1

    saved = make_summary.read_report(SUMMARY_JSON)

    if saved is None:
        return 1

    text = make_summary.make_text(saved)
    make_summary.write_text(text, FINAL_TEXT)

    search.search(records)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
