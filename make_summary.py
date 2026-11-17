"""Reads the JSON report back from disk and turns it into readable text.

The brief asks for the JSON to be read back into Python and used to build the
final summary, so this re-opens the file instead of reusing the dictionary the
program already had. That also proves the file on disk is complete.
"""

import json
import os
from datetime import datetime

WIDTH = 58


def read_history(path):
    """Return every previous run recorded in the history file.

    The file is one compact JSON object per line, which is why this uses
    read() and json.loads() line by line rather than json.load() on the whole
    file. A missing file is not an error, it just means this is the first run.
    """

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as file:
        text = file.read()

    runs = []

    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            runs.append(json.loads(line))
        except json.JSONDecodeError:
            # A half-written line from an interrupted run. Skip it, keep going.
            continue

    return runs


def record_run(report, path):
    """Append one line to the run history, so repeat runs can be compared.

    Mode "a" opens for appending and creates the file if it is not there.
    Nothing already in the file is touched, which is what makes this safe to
    run every time.
    """

    stats = report.get("request_statistics", {})
    previous = len(read_history(path))

    entry = {
        "run": previous + 1,
        "at": datetime.now().isoformat(timespec="seconds"),
        "records": report.get("total_valid_records", 0),
        "rejected": report.get("malformed_records", 0),
        "error_pct": stats.get("error_percentage", 0),
        "total_mb": report.get("transfer_statistics", {}).get("total_mb_sent", 0),
    }

    try:
        with open(path, "a", encoding="utf-8") as file:
            file.write(json.dumps(entry) + "\n")

    except OSError as error:
        print(f"ERROR writing run history: {error}")
        return None

    print(f"Run history updated: {path} (run {previous + 1})")

    return entry


def read_report(path):
    """Load the report from disk, or return None with a message."""

    try:
        with open(path, "r", encoding="utf-8") as file:
            report = json.load(file)

    except FileNotFoundError:
        print(f"ERROR: JSON report not found at {path}.")
        return None

    except json.JSONDecodeError as error:
        print(f"ERROR: JSON report is not valid: {error}")
        return None

    except OSError as error:
        print(f"ERROR reading JSON report: {error}")
        return None

    else:
        # Runs only when nothing above raised.
        if not isinstance(report, dict):
            print("ERROR: JSON report is not an object at the top level.")
            return None

        return report

    finally:
        # Runs on success and on every failure.
        print("JSON report read stage finished.")


def get(report, section, key, default="n/a"):
    """Read one value from a section without raising KeyError."""

    return report.get(section, {}).get(key, default)


def make_text(report):
    """Lay the report out as plain text. Nothing is recalculated here."""

    stats = report.get("request_statistics", {})
    timing = report.get("response_time_statistics", {})
    transfer = report.get("transfer_statistics", {})
    traffic = report.get("traffic_profile", {})
    dataset = report.get("dataset", {})

    lines = [
        "=" * WIDTH,
        "APPLICATION LOG MONITORING REPORT",
        "=" * WIDTH,
        f"Dataset file      : {dataset.get('file', 'n/a')}",
        f"Dataset source    : {dataset.get('title', 'n/a')} "
        f"({dataset.get('doi', 'n/a')})",
        f"Publisher         : {dataset.get('publisher', 'n/a')}, "
        f"{dataset.get('published', 'n/a')}",
        f"Licence           : {dataset.get('license', 'n/a')}",
        f"Log format        : {dataset.get('format', 'Apache Combined Log Format')}",
        f"Generated at      : {report.get('generated_at', 'n/a')}",
        f"Valid records     : {report.get('total_valid_records', 0)}",
        f"Malformed records : {report.get('malformed_records', 0)}",
        "",
        "REQUEST STATISTICS",
        "-" * 30,
        f"Successful requests (2xx) : {stats.get('successful_requests', 0)}",
        f"Redirects (3xx)           : {stats.get('redirects', 0)}",
        f"Client errors (4xx)       : {stats.get('client_errors', 0)}",
        f"Server errors (5xx)       : {stats.get('server_errors', 0)}",
        f"Failed requests (4xx+5xx) : {stats.get('failed_requests', 0)}",
        f"Error percentage          : {stats.get('error_percentage', 0)}%",
        "",
        "PERFORMANCE",
        "-" * 30,
    ]

    if timing.get("recorded_in_log"):
        lines.append(f"Average response time : {timing.get('average_ms')} ms")
        lines.append(
            f"Slow requests         : {timing.get('slow_request_count')} "
            f"(over {timing.get('slow_threshold_ms')} ms)"
        )
    else:
        lines.append("Average response time : not recorded by this log format")
        lines.append(timing.get("note", ""))

    lines.extend([
        f"Average response size : {transfer.get('average_bytes', 0)} bytes",
        f"Largest response      : {transfer.get('largest_response_bytes', 0)} bytes",
        f"Heavy transfers       : {transfer.get('heavy_request_count', 0)} "
        f"(over {transfer.get('heavy_threshold_bytes', 0)} bytes)",
        f"Total data sent       : {transfer.get('total_mb_sent', 0)} MB",
        "",
        "TRAFFIC PROFILE",
        "-" * 30,
        f"Distinct resources : {traffic.get('distinct_resources', 0)}",
        f"Unique client IPs  : {traffic.get('unique_client_ips', 0)}",
        f"Busiest hour       : {traffic.get('busiest_hour', 'n/a')} "
        f"({traffic.get('busiest_hour_requests', 0)} requests)",
        f"Worst hour errors  : {traffic.get('worst_error_hour', 'n/a')} "
        f"at {traffic.get('worst_error_rate_pct', 0)}% "
        f"({traffic.get('worst_error_hour_failures', 0)} of "
        f"{traffic.get('worst_error_hour_requests', 0)})",
        f"Methods used       : {traffic.get('requests_by_method', {})}",
        "",
        "OUTPUT SELF-CHECK",
        "-" * 30,
    ])

    check = report.get("hourly_self_check", {})

    if check:
        lines.extend([
            f"Hours written to CSV: {check.get('hours_written', 0)}",
            f"Requests in CSV     : {check.get('requests_in_file', 0)}",
            f"Requests analysed   : {check.get('requests_analysed', 0)}",
            f"Match               : {'yes' if check.get('matches') else 'NO'}",
        ])
    else:
        lines.append("hourly summary CSV not written, nothing to check")

    lines.extend(["", "FREQUENT ERRORS", "-" * 30])

    frequent = report.get("frequent_errors", [])

    if frequent:
        for item in frequent:
            lines.append(
                f"HTTP {item['status_code']} ({item['reason']})"
                f": {item['count']} occurrences"
            )

            for entry in item.get("top_urls", [])[:3]:
                lines.append(f"    {entry['url']}: {entry['count']}")
    else:
        lines.append("No 4xx or 5xx errors found.")

    lines.extend(["", "MOST ACCESSED RESOURCES", "-" * 30])

    resources = report.get("frequently_accessed_resources", [])

    if resources:
        for item in resources:
            lines.append(f"{item['resource']}: {item['count']} requests")
    else:
        lines.append("No resources found.")

    findings = report.get("error_findings", [])

    if findings:
        lines.extend(["", "NOTABLE FINDINGS", "-" * 30])
        lines.extend(f"- {note}" for note in findings)

    clusters = report.get("server_error_clusters", [])

    if clusters:
        lines.extend(["", "SERVER ERROR CLUSTERS", "-" * 30])

        for item in clusters:
            lines.append(
                f"HTTP {item['status_code']} on {item['url']}: "
                f"{item['count']} failures in {item['span_seconds']} seconds"
            )

    pandas = report.get("pandas_view")

    if pandas:
        lines.extend(["", "PANDAS CROSS-CHECK", "-" * 30])
        lines.append(f"Engine                : {pandas.get('engine')}")
        lines.append(f"Rows read from CSV    : {pandas.get('rows_read')}")
        lines.append(
            f"Busiest hour          : {pandas.get('busiest_hour'):02d}:00 "
            f"({pandas.get('busiest_hour_requests')} requests)"
        )
        lines.append(
            f"Worst hour for errors : {pandas.get('worst_hour'):02d}:00 "
            f"at {pandas.get('worst_hour_error_pct')}%"
        )
        lines.append(
            f"JSON round trip       : "
            f"{'ok' if pandas.get('json_round_trip_ok') else 'FAILED'}"
        )
        agrees = pandas.get("agrees_with_stdlib")

        if agrees is not None:
            lines.append(
                f"Matches csv.writer    : {'yes' if agrees else 'no'}"
            )

    rejected = report.get("rejected_records", {})

    if rejected.get("total_rejected"):
        lines.extend(["", "MALFORMED RECORDS", "-" * 30])
        lines.append(f"Rejected: {rejected['total_rejected']}")

        for reason_text, count in rejected.get("by_reason", {}).items():
            lines.append(f"  {reason_text}: {count}")

    return "\n".join(lines)


def write_text(text, path):
    """Print the summary and save it to a text file.

    writelines() takes a list of strings and writes them in order. It does not
    add line endings for you, so keepends=True keeps the ones make_text put in.
    """

    print("\n" + text)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8") as file:
            file.writelines(text.splitlines(keepends=True))
            file.write("\n")

    except OSError as error:
        print(f"ERROR writing summary: {error}")
        return None

    print(f"\nHuman-readable report saved: {path}")

    return path
