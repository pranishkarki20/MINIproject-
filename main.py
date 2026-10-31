
import csv
import json
import os
from collections import Counter
from datetime import datetime

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

INPUT_FILE = "sample-web-logs.csv"
OUTPUT_DIR = "output"

PROCESSED_FILE = os.path.join(
    OUTPUT_DIR, "processed_logs.csv"
)
JSON_FILE = os.path.join(
    OUTPUT_DIR, "summary_report.json"
)
SUMMARY_FILE = os.path.join(
    OUTPUT_DIR, "final_summary.txt"
)

SLOW_RESPONSE_THRESHOLD = 1000  # milliseconds


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_value(row, possible_names, default=""):
    """Read a field using alternative column names."""

    for name in possible_names:
        for key, value in row.items():
            if key and key.strip().lower() == name.lower():
                if value is not None and str(value).strip():
                    return str(value).strip()

    return default


def classify_status(status_code):
    """Classify HTTP response status codes."""

    if 200 <= status_code < 300:
        return "Successful"
    elif 300 <= status_code < 400:
        return "Redirect"
    elif 400 <= status_code < 500:
        return "Client Error"
    elif 500 <= status_code < 600:
        return "Server Error"
    else:
        return "Unknown"


def parse_response_time(value):
    """Convert response time to milliseconds."""

    value = str(value).strip().lower()
    value = value.replace("milliseconds", "ms")
    value = value.replace("millisecond", "ms")

    if value.endswith("ms"):
        return float(value[:-2].strip())

    if value.endswith("s"):
        return float(value[:-1].strip()) * 1000

    # Assumption: numeric values are already milliseconds.
    return float(value)


def parse_timestamp(value):
    """Validate a timestamp when one is supplied."""

    value = value.strip()

    if not value:
        return ""

    # Accept common web-log timestamp formats.
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%d/%b/%Y:%H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
    ]

    for fmt in formats:
        try:
            datetime.strptime(value, fmt)
            return value
        except ValueError:
            continue

    raise ValueError("Invalid timestamp format")


# --------------------------------------------------
# READ AND PROCESS DATASET
# --------------------------------------------------

def process_logs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    processed_records = []
    rejected_records = []

    successful = 0
    redirects = 0
    client_errors = 0
    server_errors = 0
    failed_requests = 0

    error_counter = Counter()
    resource_counter = Counter()
    status_counter = Counter()

    slow_requests = []
    total_response_time = 0.0
    response_time_count = 0

    try:
        # Read original CSV using the with open() context manager.
        with open(
            INPUT_FILE, "r", encoding="utf-8-sig", newline=""
        ) as file:

            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise ValueError("CSV file has no header row")

            required_columns = {
                "status_code": [
                    "status_code", "status", "http_status",
                    "http_status_code", "statuscode"
                ],
                "url": [
                    "url", "request", "resource", "path",
                    "request_url", "request_uri"
                ],
            }

            headers = {
                h.strip().lower()
                for h in reader.fieldnames if h
            }

            for field, aliases in required_columns.items():
                if not any(a in headers for a in aliases):
                    raise ValueError(
                        f"Missing required column: {field}. "
                        f"Available columns: {reader.fieldnames}"
                    )

            for line_number, row in enumerate(reader, start=2):

                try:
                    if not row or not any(
                        str(v or "").strip() for v in row.values()
                    ):
                        raise ValueError("Empty record")

                    timestamp = get_value(
                        row,
                        ["timestamp", "time", "datetime", "@timestamp"]
                    )

                    ip = get_value(
                        row,
                        ["ip", "ip_address", "client_ip",
                         "remote_addr", "host", "client"]
                    )

                    method = get_value(
                        row,
                        ["method", "request_method", "http_method"],
                        "UNKNOWN"
                    )

                    url = get_value(
                        row,
                        ["url", "request", "resource", "path",
                         "request_url", "request_uri"]
                    )

                    status_text = get_value(
                        row,
                        ["status_code", "status", "http_status",
                         "http_status_code", "statuscode"]
                    )

                    response_text = get_value(
                        row,
                        ["response_time", "response_time_ms",
                         "latency", "duration", "time_taken"],
                        "0"
                    )

                    message = get_value(
                        row,
                        ["error_message", "error", "message",
                         "error_info", "reason"]
                    )

                    if not url:
                        raise ValueError("Missing requested resource")

                    if not status_text:
                        raise ValueError("Missing HTTP status code")

                    # Validate and convert the status code.
                    status_code = int(status_text)

                    if not 100 <= status_code <= 599:
                        raise ValueError("Invalid HTTP status code")

                    if timestamp:
                        timestamp = parse_timestamp(timestamp)

                    response_time = parse_response_time(
                        response_text
                    )

                    if response_time < 0:
                        raise ValueError("Negative response time")

                    category = classify_status(status_code)

                    # Count successful requests, errors and redirects.
                    if category == "Successful":
                        successful += 1
                    elif category == "Redirect":
                        redirects += 1
                    elif category == "Client Error":
                        client_errors += 1
                        error_counter[status_code] += 1
                    elif category == "Server Error":
                        server_errors += 1
                        error_counter[status_code] += 1
                    else:
                        failed_requests += 1

                    # Treat HTTP 4xx and 5xx as failed requests.
                    if status_code >= 400:
                        failed_requests += 0
                        if not message:
                            message = f"HTTP {status_code} error"

                    status_counter[status_code] += 1
                    resource_counter[url] += 1

                    total_response_time += response_time
                    response_time_count += 1

                    record = {
                        "timestamp": timestamp,
                        "ip": ip,
                        "method": method,
                        "url": url,
                        "status_code": status_code,
                        "response_time_ms": round(
                            response_time, 2
                        ),
                        "category": category,
                        "error_message": message,
                    }

                    processed_records.append(record)

                    if response_time >= SLOW_RESPONSE_THRESHOLD:
                        slow_requests.append(record)

                except (ValueError, TypeError, AttributeError) as exc:
                    # Keep malformed records for a separate report.
                    rejected_records.append({
                        "line_number": line_number,
                        "reason": str(exc),
                        "original_record": row,
                    })
                    continue

            else:
                # Runs when the CSV loop completes normally.
                print("CSV processing completed.")

    except FileNotFoundError:
        print(f"ERROR: Dataset not found: {INPUT_FILE}")
        print("Put your CSV dataset in the data folder.")
        return

    except PermissionError:
        print("ERROR: Permission denied while reading the dataset.")
        return

    except csv.Error as exc:
        print(f"ERROR: CSV format problem: {exc}")
        return

    except (ValueError, UnicodeDecodeError) as exc:
        print(f"ERROR: Could not process the dataset: {exc}")
        return

    finally:
        # Demonstrates finally: this executes on normal exit or error.
        print("Dataset reading stage finished.")

    # --------------------------------------------------
    # WRITE PROCESSED CSV
    # --------------------------------------------------

    csv_fields = [
        "timestamp", "ip", "method", "url",
        "status_code", "response_time_ms",
        "category", "error_message"
    ]

    try:
        with open(
            PROCESSED_FILE, "w", encoding="utf-8",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file, fieldnames=csv_fields
            )
            writer.writeheader()
            writer.writerows(processed_records)

        print(f"Processed CSV saved: {PROCESSED_FILE}")

    except (OSError, csv.Error) as exc:
        print(f"ERROR writing processed CSV: {exc}")
        return

    # --------------------------------------------------
    # CALCULATE STATISTICS
    # --------------------------------------------------

    total_records = len(processed_records)
    total_errors = client_errors + server_errors

    error_percentage = (
        (total_errors / total_records) * 100
        if total_records else 0
    )

    average_response_time = (
        total_response_time / response_time_count
        if response_time_count else 0
    )

    # --------------------------------------------------
    # GENERATE STRUCTURED JSON REPORT
    # --------------------------------------------------

    report = {
        "dataset": INPUT_FILE,
        "generated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "total_valid_records": total_records,
        "malformed_records": len(rejected_records),
        "request_statistics": {
            "successful_requests": successful,
            "redirects": redirects,
            "client_errors": client_errors,
            "server_errors": server_errors,
            "failed_requests": client_errors + server_errors,
            "unknown_status_requests": failed_requests,
            "error_percentage": round(error_percentage, 2),
        },
        "response_time_statistics": {
            "average_ms": round(average_response_time, 2),
            "slow_threshold_ms": SLOW_RESPONSE_THRESHOLD,
            "slow_request_count": len(slow_requests),
        },
        "frequent_errors": [
            {"status_code": code, "count": count}
            for code, count in error_counter.most_common(10)
        ],
        "frequently_accessed_resources": [
            {"resource": url, "count": count}
            for url, count in resource_counter.most_common(10)
        ],
        "status_code_distribution": {
            str(code): count
            for code, count in sorted(status_counter.items())
        },
        "slow_requests": slow_requests[:20],
        "rejected_records": rejected_records[:100],
    }

    try:
        with open(
            JSON_FILE, "w", encoding="utf-8"
        ) as file:
            json.dump(report, file, indent=4)

        print(f"JSON report saved: {JSON_FILE}")

    except (OSError, TypeError, ValueError) as exc:
        print(f"ERROR writing JSON report: {exc}")
        return

    # --------------------------------------------------
    # READ JSON BACK AND GENERATE HUMAN-READABLE SUMMARY
    # --------------------------------------------------

    try:
        with open(
            JSON_FILE, "r", encoding="utf-8"
        ) as file:
            saved_report = json.load(file)

    except FileNotFoundError:
        print("ERROR: JSON report was not found.")
        return

    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON report: {exc}")
        return

    except OSError as exc:
        print(f"ERROR reading JSON report: {exc}")
        return

    else:
        stats = saved_report["request_statistics"]
        timing = saved_report["response_time_statistics"]

        lines = [
            "=" * 55,
            "APPLICATION LOG MONITORING REPORT",
            "=" * 55,
            f"Dataset: {saved_report['dataset']}",
            f"Valid records: {saved_report['total_valid_records']}",
            f"Malformed records: {saved_report['malformed_records']}",
            "",
            "REQUEST STATISTICS",
            "-" * 30,
            f"Successful requests: {stats['successful_requests']}",
            f"Redirects: {stats['redirects']}",
            f"Client errors (4xx): {stats['client_errors']}",
            f"Server errors (5xx): {stats['server_errors']}",
            f"Failed requests (4xx + 5xx): {stats['failed_requests']}",
            f"Error percentage: {stats['error_percentage']}%",
            "",
            "RESPONSE TIMES",
            "-" * 30,
            f"Average response time: {timing['average_ms']} ms",
            f"Slow requests: {timing['slow_request_count']}",
            "",
            "FREQUENT ERRORS",
            "-" * 30,
        ]

        if saved_report["frequent_errors"]:
            for item in saved_report["frequent_errors"]:
                lines.append(
                    f"HTTP {item['status_code']}: {item['count']} occurrences"
                )
        else:
            lines.append("No 4xx or 5xx errors found.")

        lines.extend([
            "",
            "MOST ACCESSED RESOURCES",
            "-" * 30,
        ])

        if saved_report["frequently_accessed_resources"]:
            for item in saved_report[
                "frequently_accessed_resources"
            ]:
                lines.append(
                    f"{item['resource']}: {item['count']} requests"
                )
        else:
            lines.append("No resources found.")

        summary_text = "\n".join(lines)

        print("\n" + summary_text)

        try:
            with open(
                SUMMARY_FILE, "w", encoding="utf-8"
            ) as file:
                file.write(summary_text + "\n")

            print(f"\nHuman-readable report saved: {SUMMARY_FILE}")

        except OSError as exc:
            print(f"ERROR writing summary: {exc}")

    finally:
        print("Report generation stage finished.")

    # --------------------------------------------------
    # USER SEARCH: STATUS CODE OR ERROR TYPE
    # --------------------------------------------------

    search_logs(processed_records)


def search_logs(records):
    """Find records by HTTP status code or error type."""

    print("\n" + "=" * 55)
    print("SEARCH LOG RECORDS")
    print("=" * 55)
    print("1. Search by HTTP status code (e.g. 404)")
    print("2. Search by error type (client/server)")
    print("3. Exit")

    while True:
        choice = input("\nEnter your choice: ").strip()

        if choice == "3":
            print("Search finished.")
            break

        elif choice == "1":
            status_input = input(
                "Enter HTTP status code: "
            ).strip()

            try:
                status = int(status_input)

                if not 100 <= status <= 599:
                    raise ValueError(
                        "Status code must be between 100 and 599."
                    )

            except ValueError as exc:
                print(f"Invalid status code: {exc}")
                continue

            matches = [
                r for r in records
                if r["status_code"] == status
            ]

        elif choice == "2":
            error_type = input(
                "Enter client, server, or all: "
            ).strip().lower()

            if error_type == "client":
                matches = [
                    r for r in records
                    if r["category"] == "Client Error"
                ]
            elif error_type == "server":
                matches = [
                    r for r in records
                    if r["category"] == "Server Error"
                ]
            elif error_type == "all":
                matches = [
                    r for r in records
                    if r["category"] in (
                        "Client Error", "Server Error"
                    )
                ]
            else:
                print("Enter client, server, or all.")
                continue

        else:
            print("Please enter 1, 2, or 3.")
            continue

        print(f"\nMatching records: {len(matches)}")

        for record in matches[:20]:
            print(
                f"{record['timestamp']} | "
                f"{record['ip']} | "
                f"{record['method']} | "
                f"{record['url']} | "
                f"HTTP {record['status_code']} | "
                f"{record['response_time_ms']} ms | "
                f"{record['category']}"
            )

        if len(matches) > 20:
            print("Showing the first 20 matches only.")


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------

if __name__ == "__main__":
    process_logs()
