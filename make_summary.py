
import json
import os

WIDTH = 58


def read_report(path):

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
        if not isinstance(report, dict):
            print("ERROR: JSON report is not an object at the top level.")
            return None

        return report

    finally:
        print("JSON report read stage finished.")


def get(report, section, key, default="n/a"):

    return report.get(section, {}).get(key, default)


def make_text(report):

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
        f"Busiest hour       : {traffic.get('busiest_hour', 'n/a')}",
        f"Methods used       : {traffic.get('requests_by_method', {})}",
        "",
        "FREQUENT ERRORS",
        "-" * 30,
    ])

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

    rejected = report.get("rejected_records", {})

    if rejected.get("total_rejected"):
        lines.extend(["", "MALFORMED RECORDS", "-" * 30])
        lines.append(f"Rejected: {rejected['total_rejected']}")

        for reason_text, count in rejected.get("by_reason", {}).items():
            lines.append(f"  {reason_text}: {count}")

    return "\n".join(lines)


def write_text(text, path):

    print("\n" + text)

    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(text + "\n")

    except OSError as error:
        print(f"ERROR writing summary: {error}")
        return None

    print(f"\nHuman-readable report saved: {path}")

    return path
